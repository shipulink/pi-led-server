import array
import time

import app.dma as dma
import app.gpio as gpio
import app.led_frame_data as fd
import app.memory_utils as mu
import app.pwm as pwm

PWM_CLK_SRC = pwm.CLK_SRC_PLLD
PWM_CLK_DIV_INT = 5
PWM_CLK_DIV_FRAC = 0
PWM_CYCLES = 150

PLAY_SECONDS = 5
DMA_CH = 2

GPIO_INFO = gpio.GpioInfo(18)

DMA_WAITS_ZERO = 0 << 21
DMA_WAITS_ONE = 20 << 21

DMA_FLAGS_DATA = dma.DMA_NO_WIDE_BURSTS | dma.DMA_WAIT_RESP
DMA_FLAGS_WAIT = dma.DMA_NO_WIDE_BURSTS | dma.DMA_WAIT_RESP | dma.DMA_SRC_IGNORE
DMA_FLAGS_PWM = dma.DMA_NO_WIDE_BURSTS | dma.DMA_SRC_IGNORE | dma.DMA_PERMAP | dma.DMA_DEST_DREQ

# Build control array from incoming bytes
ints = [
    # 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00
    0x00, 0x11, 0x00, 0x11, 0x00, 0x00, 0x00, 0x00, 0x11, 0x00, 0x11, 0x00, 0x11, 0x00, 0x00, 0x00, 0x00, 0x11
    # 0x00, 0xFF, 0x00, 0xFF, 0x00, 0x00, 0x00, 0x00, 0xFF, 0x00, 0xFF, 0x00, 0xFF, 0x00, 0x00, 0x00, 0x00, 0xFF
    # 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF
]
byte_arr = array.array("B", ints)

dma_data = fd.LedDmaFrameData(int(len(byte_arr) / 3))

# Allocate enough memory for all the CBs.
shared_mem = mu.create_phys_contig_int_view(256)

# CBs that don't need dedicated space for source data
CB_IDLE_WAIT = dma.ControlBlock3(shared_mem, 0)
CB_DATA_WAIT = dma.ControlBlock3(shared_mem, 8)
CB_DATA_ONE_WAIT1 = dma.ControlBlock3(shared_mem, 16)
CB_DATA_ONE_WAIT2 = dma.ControlBlock3(shared_mem, 24)
CB_DATA_UPD = dma.ControlBlock3(shared_mem, 32)  # Updates its own src addr and CB_DATA_WAIT's next CB addr via stride

# CBs that need dedicated space for source data
CB_IDLE_CLR = dma.ControlBlock3(shared_mem, 48)
CB_DATA_CLR = dma.ControlBlock3(shared_mem, 64)
CB_DATA_STOP = dma.ControlBlock3(shared_mem, 80)
CB_DATA_ZERO_SET = dma.ControlBlock3(shared_mem, 96)
CB_DATA_ONE_SET = dma.ControlBlock3(shared_mem, 112)

# Configure idle loop
CB_IDLE_WAIT.set_transfer_information(DMA_FLAGS_PWM)
CB_IDLE_WAIT.set_destination_addr(pwm.PWM_BASE_BUS + pwm.PWM_FIFO)
CB_IDLE_WAIT.set_next_cb(CB_IDLE_CLR.addr)

CB_IDLE_CLR.set_transfer_information(DMA_FLAGS_DATA)
CB_IDLE_CLR.write_word_to_source_data(0x0, 1 << GPIO_INFO.flip_shift)  # pin 18
CB_IDLE_CLR.set_destination_addr(gpio.GPIO_BASE_BUS + GPIO_INFO.clr_reg_offset)
CB_IDLE_CLR.set_next_cb(CB_IDLE_WAIT.addr)

# Configure data loop
CB_DATA_CLR.set_transfer_information(DMA_FLAGS_DATA)
CB_DATA_CLR.write_word_to_source_data(0, 1 << GPIO_INFO.flip_shift)  # pin 18
CB_DATA_CLR.set_destination_addr(gpio.GPIO_BASE_BUS + GPIO_INFO.clr_reg_offset)
CB_DATA_CLR.set_next_cb(CB_DATA_UPD.addr)

src_stride = int(dma_data.view_len / 2 * 4)
dest_stride = CB_DATA_WAIT.addr + 0x14 - (CB_DATA_UPD.addr + 0x4)
CB_DATA_UPD.set_transfer_information(DMA_FLAGS_DATA | dma.DMA_TD_MODE)
CB_DATA_UPD.set_source_addr(dma_data.base_addrs[0])
CB_DATA_UPD.set_destination_addr(CB_DATA_UPD.addr + 0x4)
CB_DATA_UPD.set_transfer_length_stride(4, 2)
CB_DATA_UPD.set_stride(src_stride, dest_stride)
CB_DATA_UPD.set_next_cb(CB_DATA_WAIT.addr)

CB_DATA_WAIT.set_transfer_information(DMA_FLAGS_PWM)
CB_DATA_WAIT.set_destination_addr(pwm.PWM_BASE_BUS + pwm.PWM_FIFO)

CB_DATA_STOP.set_transfer_information(DMA_FLAGS_DATA)
CB_DATA_STOP.write_word_to_source_data(0, CB_IDLE_WAIT.addr)
CB_DATA_STOP.set_destination_addr(CB_IDLE_CLR.addr + 0x14)
CB_DATA_STOP.set_next_cb(CB_IDLE_WAIT.addr)

CB_DATA_ZERO_SET.set_transfer_information(DMA_FLAGS_DATA | DMA_WAITS_ZERO)
CB_DATA_ZERO_SET.init_source_data(8)
CB_DATA_ZERO_SET.write_word_to_source_data(1, 1 << GPIO_INFO.flip_shift)  # pin 18
CB_DATA_ZERO_SET.set_destination_addr(gpio.GPIO_BASE_BUS + GPIO_INFO.set_reg_offset)
CB_DATA_ZERO_SET.set_next_cb(CB_DATA_CLR.addr)

CB_DATA_ONE_SET.set_transfer_information(DMA_FLAGS_DATA)
CB_DATA_ONE_SET.write_word_to_source_data(0, 1 << GPIO_INFO.flip_shift)  # pin 18
CB_DATA_ONE_SET.set_destination_addr(gpio.GPIO_BASE_BUS + GPIO_INFO.set_reg_offset)
CB_DATA_ONE_SET.set_next_cb(CB_DATA_ONE_WAIT1.addr)

CB_DATA_ONE_WAIT1.set_transfer_information(DMA_FLAGS_WAIT | DMA_WAITS_ONE)
CB_DATA_ONE_WAIT1.set_destination_addr(pwm.PWM_BASE_BUS + pwm.PWM_FIFO)
CB_DATA_ONE_WAIT1.set_next_cb(CB_DATA_ONE_WAIT2.addr)

CB_DATA_ONE_WAIT2.set_transfer_information(DMA_FLAGS_WAIT | DMA_WAITS_ONE)
CB_DATA_ONE_WAIT2.set_destination_addr(pwm.PWM_BASE_BUS + pwm.PWM_FIFO)
CB_DATA_ONE_WAIT2.set_next_cb(CB_DATA_CLR.addr)

dma_data.set_cb_addrs(CB_DATA_ZERO_SET.addr, CB_DATA_ONE_SET.addr, CB_DATA_STOP.addr)
dma_data.populate_with_data(byte_arr)
# dma_data.print_debug_info()

pwm.configure_and_start_pwm(DMA_CH, PWM_CLK_SRC, PWM_CLK_DIV_INT, PWM_CLK_DIV_FRAC, PWM_CYCLES)
gpio.set_pin_fnc_to_output(GPIO_INFO)

#############
# Start DMA #
#############
dma.activate_channel_with_cb(DMA_CH, CB_IDLE_WAIT.addr)
time.sleep(0.1)

start = time.time()
while time.time() - start < PLAY_SECONDS:
    CB_IDLE_CLR.set_next_cb(CB_DATA_CLR.addr)
    time.sleep(.01)

time.sleep(0.1)

pwm.stop_pwm(DMA_CH, PWM_CLK_SRC)
