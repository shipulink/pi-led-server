import app.dma as dma
import app.gpio as gpio
import app.led_frame_data as fd
import app.memory_utils as mu
import app.pwm as pwm

PWM_CLK_SRC = pwm.CLK_SRC_PLLD
PWM_CLK_DIV_INT = 5
PWM_CLK_DIV_FRAC = 0
PWM_CYCLES = 75
DMA_CH = 2
GPIO_INFO_PIN18 = gpio.GpioInfo(18)
GPIO_INFO_PIN15 = gpio.GpioInfo(15)
DMA_WAITS = 27 << 21

DMA_FLAGS_PWM = dma.DMA_TI_NO_WIDE_BURSTS | dma.DMA_TI_SRC_IGNORE | dma.DMA_TI_PERMAP | dma.DMA_TI_DEST_DREQ

MS_BASE = 0x20000000
MS_BASE_BUS = 0x7e000000
MS_MBOX_REG_OFFSET = 0xA0


class NeopixelDriver:
    def __init__(self, num_leds, gpio_pins: [gpio.GpioInfo]):
        self.dma_data = fd.LedDmaFrameData(num_leds)

        # SET and CLR registers are spaced as follows, spanning 5 registers:
        # SET  SET  --   CLR  CLR
        # 1C   20   24   28   2C
        # MS_MBOX_0 - MS_MBOX_7 are peripheral registers usable for storing this data.
        # We will only need MS_MBOX_0 - MS_MBOX_4.
        # The first two registers will be used to always set / clear gpio pins, so the appropriate bits in MS_MBOX_0 and
        # MS_MBOX_1 should just statically be set for this purpose. MS_MBOX_3 and MS_MBOX_4 will be used for optionally
        # clearing the GPIO pins.

        with mu.mmap_dev_mem(MS_BASE) as m:
            mu.write_word_to_byte_array(
                m, MS_MBOX_REG_OFFSET + GPIO_INFO_PIN18.set_clr_register_index,
                   1 << GPIO_INFO_PIN18.pin_flip_bit_shift | 1 << GPIO_INFO_PIN15.pin_flip_bit_shift)

        # Allocate enough memory for all the CBs.
        self.shared_mem = mu.create_aligned_phys_contig_int_view(32, 32)

        # CBs
        self.cb_idle_wait = dma.ControlBlock()
        self.cb_idle_clr = dma.ControlBlock()

        self.cb_data_advance = dma.ControlBlock(self.shared_mem, 0)  # Advances its own SRC_ADDR and cb_data_upd's SRC_ADDR
        self.cb_data_upd = dma.ControlBlock(self.shared_mem, 24)  # Writes the next bit to be copied to GPIO into MS_MBOX

        self.cb_data_wait1 = dma.ControlBlock()
        self.cb_data_set_clr = dma.ControlBlock()
        self.cb_data_wait2 = dma.ControlBlock()
        self.cb_data_clr = dma.ControlBlock(self.shared_mem, 8)  # Clears GPIO pins and goes to cb_data_advance or CB_PAUSE

        self.cb_pause = dma.ControlBlock()  # Resets cb_idle_clr's NEXT_CB_ADDR to get into the idle CB loop

        # Configure idle loop
        self.cb_idle_wait.set_transfer_information(DMA_FLAGS_PWM)
        self.cb_idle_wait.set_destination_addr(pwm.PWM_BASE_BUS + pwm.PWM_FIFO)
        self.cb_idle_wait.set_next_cb_addr(self.cb_idle_clr.addr)

        self.cb_idle_clr.set_transfer_information(dma.DMA_TI_SRC_INC | dma.DMA_TI_DEST_INC)
        self.cb_idle_clr.set_transfer_length(8)
        self.cb_idle_clr.set_source_addr(MS_BASE_BUS + MS_MBOX_REG_OFFSET)
        self.cb_idle_clr.set_destination_addr(gpio.GPIO_BASE_BUS + gpio.GPCLR0)
        self.cb_idle_clr.set_next_cb_addr(self.cb_idle_wait.addr)

        # Configure data loop
        cb_data_advance_src_addr = self.cb_data_advance.addr + 0x4
        src_stride = 4
        dest_stride = 48
        self.cb_data_advance.set_transfer_information(dma.DMA_TI_TD_MODE)
        self.cb_data_advance.set_source_addr(self.dma_data.start_address)
        self.cb_data_advance.set_destination_addr(cb_data_advance_src_addr)
        self.cb_data_advance.set_transfer_length_stride(4, 3)
        self.cb_data_advance.set_stride(src_stride, dest_stride)
        self.cb_data_advance.set_next_cb_addr(self.cb_data_upd.addr)

        self.cb_data_upd.set_transfer_information(dma.DMA_TI_SRC_INC | dma.DMA_TI_DEST_INC)
        self.cb_data_upd.set_transfer_length(8)
        self.cb_data_upd.set_destination_addr(MS_BASE_BUS + MS_MBOX_REG_OFFSET + 12)  # writes GPIO CLR data to MS_MBOX_3,4
        self.cb_data_upd.set_next_cb_addr(self.cb_data_wait1.addr)

        self.cb_data_wait1.set_transfer_information(DMA_FLAGS_PWM)
        self.cb_data_wait1.set_destination_addr(pwm.PWM_BASE_BUS + pwm.PWM_FIFO)
        self.cb_data_wait1.set_next_cb_addr(self.cb_data_set_clr.addr)

        self.cb_data_set_clr.set_transfer_information(
            dma.DMA_TI_NO_WIDE_BURSTS | dma.DMA_TI_DEST_INC | dma.DMA_TI_SRC_INC | DMA_WAITS)
        self.cb_data_set_clr.set_transfer_length(20)
        self.cb_data_set_clr.set_source_addr(MS_BASE_BUS + MS_MBOX_REG_OFFSET)
        self.cb_data_set_clr.set_destination_addr(gpio.GPIO_BASE_BUS + gpio.GPSET0)
        self.cb_data_set_clr.set_next_cb_addr(self.cb_data_wait2.addr)

        self.cb_data_wait2.set_transfer_information(DMA_FLAGS_PWM)
        self.cb_data_wait2.set_destination_addr(pwm.PWM_BASE_BUS + pwm.PWM_FIFO)
        self.cb_data_wait2.set_next_cb_addr(self.cb_data_clr.addr)

        self.cb_data_clr.set_transfer_information(dma.DMA_TI_NO_WIDE_BURSTS | dma.DMA_TI_SRC_INC | dma.DMA_TI_DEST_INC)
        self.cb_data_clr.set_transfer_length(8)
        self.cb_data_clr.set_source_addr(MS_BASE_BUS + MS_MBOX_REG_OFFSET)
        self.cb_data_clr.set_destination_addr(gpio.GPIO_BASE_BUS + gpio.GPCLR0)

        self.cb_pause.set_transfer_length(4)
        self.cb_pause.write_word_to_source_data(0, self.cb_idle_wait.addr)
        self.cb_pause.set_destination_addr(self.cb_idle_clr.addr + 0x14)
        self.cb_pause.set_next_cb_addr(self.cb_idle_clr.addr)

        self.dma_data.set_cb_addrs(self.cb_data_advance.addr, self.cb_pause.addr)

        self.gpio_pins = gpio_pins

    def start(self):
        pwm.configure_and_start_pwm(DMA_CH, PWM_CLK_SRC, PWM_CLK_DIV_INT, PWM_CLK_DIV_FRAC, PWM_CYCLES)
        gpio.set_pins_to_output([GPIO_INFO_PIN15, GPIO_INFO_PIN18])
        dma.activate_channel_with_cb(DMA_CH, self.cb_idle_wait.addr)

    @staticmethod
    def stop():
        pwm.stop_pwm(DMA_CH, PWM_CLK_SRC)

    def send_frame(self, frame):
        self.dma_data.populate_with_data(frame, self.gpio_pins)
        self.cb_idle_clr.set_next_cb_addr(self.cb_data_advance.addr)
