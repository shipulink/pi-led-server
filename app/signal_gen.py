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
PWM_CYCLES = 75
PLAY_SECONDS = 2
DMA_CH = 2
GPIO_INFO_PIN18 = gpio.GpioInfo(18)
GPIO_INFO_PIN15 = gpio.GpioInfo(15)
DMA_WAITS = 27 << 21

DMA_FLAGS_PWM = dma.DMA_NO_WIDE_BURSTS | dma.DMA_SRC_IGNORE | dma.DMA_PERMAP | dma.DMA_DEST_DREQ

MS_BASE = 0x20000000
MS_BASE_BUS = 0x7e000000
MS_MBOX_REG_OFFSET = 0xA0

# Build arrays of incoming bytes
byte_arr1 = array.array("B", [
    # 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00
    0x55, 0x55, 0x55, 0x55, 0x55, 0x55, 0x55, 0x55, 0x55, 0x55, 0x55, 0x55, 0x55, 0x55, 0x55, 0x55, 0x55, 0x55
])
byte_arr2 = array.array("B", [
    # 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00
    # 0xAA, 0xAA, 0xAA, 0xAA, 0xAA, 0xAA, 0xAA, 0xAA, 0xAA, 0xAA, 0xAA, 0xAA, 0xAA, 0xAA, 0xAA, 0xAA, 0xAA, 0xAA
    # 0x55, 0x55, 0x55, 0x55, 0x55, 0x55, 0x55, 0x55, 0x55, 0x55, 0x55, 0x55, 0x55, 0x55, 0x55, 0x55, 0x55, 0x55
    0x00, 0x11, 0x00, 0x11, 0x00, 0x00, 0x00, 0x00, 0x11, 0x00, 0x11, 0x00, 0x11, 0x00, 0x00, 0x00, 0x00, 0x11
    # 0x00, 0xFF, 0x00, 0xFF, 0x00, 0x00, 0x00, 0x00, 0xFF, 0x00, 0xFF, 0x00, 0xFF, 0x00, 0x00, 0x00, 0x00, 0xFF
    # 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF
])
num_leds = int(len(byte_arr1) / 3)
dma_data = fd.LedDmaFrameData2(num_leds)
dma_data.populate_with_data(byte_arr1, GPIO_INFO_PIN15)
dma_data.populate_with_data(byte_arr2, GPIO_INFO_PIN18)

# SET and CLR registers are spaced as follows, spanning 4 registers:
# SET -   -   CLR
# 1C  20  24  28
# MS_MBOX_0 - MS_MBOX_7 are peripheral registers usable for storing this data. We will only need MS_MBOX_0 - MS_MBOX_3.
# The first register will be used to always set / clear gpio pins, so the appropriate bits in MS_MBOX_0 should just
# statically be set. The fourth register will be used to optionally clear gpio pins to create a "zero" square wave.

with mu.mmap_dev_mem(MS_BASE) as m:
    print(mu.print_byte_array_as_hex_words(m, 2, MS_MBOX_REG_OFFSET))
    mu.write_word_to_byte_array(
        m, MS_MBOX_REG_OFFSET + GPIO_INFO_PIN18.set_clr_register_index,
        1 << GPIO_INFO_PIN18.pin_flip_bit_shift | 1 << GPIO_INFO_PIN15.pin_flip_bit_shift)
    print(mu.print_byte_array_as_hex_words(m, 2, MS_MBOX_REG_OFFSET))

# Allocate enough memory for all the CBs.
shared_mem = mu.create_aligned_phys_contig_int_view(384, 32)

# CBs
CB_IDLE_WAIT = dma.ControlBlock3(shared_mem, 0)
CB_IDLE_CLR = dma.ControlBlock3(shared_mem, 8)

CB_DATA_ADVANCE = dma.ControlBlock3(shared_mem, 16)  # Advances its own SRC_ADDR and CB_DATA_UPD's SRC_ADDR
CB_DATA_UPD = dma.ControlBlock3(shared_mem, 24)  # Writes the next bit to be copied to GPIO into MS_MBOX
CB_DATA_ADVANCE2 = dma.ControlBlock3(shared_mem, 32)  # Advances its own SRC_ADDR and NEXT_CB_ADDR of CB_DATA_WAIT2

CB_DATA_SET_CLR = dma.ControlBlock3(shared_mem, 40)
CB_DATA_WAIT1 = dma.ControlBlock3(shared_mem, 48)
CB_DATA_CLR = dma.ControlBlock3(shared_mem, 56)
CB_DATA_WAIT2 = dma.ControlBlock3(shared_mem, 64)  # Waits and either goes to CB_DATA_ADVANCE or CB_DATA_PAUSE

CB_PAUSE = dma.ControlBlock3(shared_mem, 72)  # Resets CB_IDLE_CLR's NEXT_CB_ADDR to get into the idle CB loop

# Configure idle loop
CB_IDLE_WAIT.set_transfer_information(DMA_FLAGS_PWM)
CB_IDLE_WAIT.set_destination_addr(pwm.PWM_BASE_BUS + pwm.PWM_FIFO)
CB_IDLE_WAIT.set_next_cb(CB_IDLE_CLR.addr)

CB_IDLE_CLR.set_transfer_information(dma.DMA_SRC_INC | dma.DMA_DEST_INC)
CB_IDLE_CLR.set_transfer_length(8)
CB_IDLE_CLR.set_source_addr(MS_BASE_BUS + MS_MBOX_REG_OFFSET)
CB_IDLE_CLR.set_destination_addr(gpio.GPIO_BASE_BUS + gpio.GPCLR0_REG_OFFSET)
CB_IDLE_CLR.set_next_cb(CB_IDLE_WAIT.addr)

# Configure data loop
cb_data_advance_src_addr = CB_DATA_ADVANCE.addr + 0x4
cb_data_upd_src_addr = CB_DATA_UPD.addr + 0x4
src_stride = 4
dest_stride = cb_data_upd_src_addr - cb_data_advance_src_addr
CB_DATA_ADVANCE.set_transfer_information(dma.DMA_TD_MODE)
CB_DATA_ADVANCE.set_source_addr(dma_data.start_address)
CB_DATA_ADVANCE.set_destination_addr(cb_data_advance_src_addr)
CB_DATA_ADVANCE.set_transfer_length_stride(4, 2)
CB_DATA_ADVANCE.set_stride(src_stride, dest_stride)
CB_DATA_ADVANCE.set_next_cb(CB_DATA_UPD.addr)

CB_DATA_UPD.set_transfer_information(dma.DMA_SRC_INC | dma.DMA_DEST_INC)
CB_DATA_UPD.set_transfer_length(8)
CB_DATA_UPD.set_destination_addr(MS_BASE_BUS + MS_MBOX_REG_OFFSET + 12)  # overwrite MS_MBOX_3,4 with GPIO CLR data
CB_DATA_UPD.set_next_cb(CB_DATA_ADVANCE2.addr)

cb_data_advance2_src_addr = CB_DATA_ADVANCE2.addr + 0x4
cb_data_wait2_next_cb_addr = CB_DATA_WAIT2.addr + 0x14
src_stride2 = 8
dest_stride2 = cb_data_wait2_next_cb_addr - cb_data_advance2_src_addr
CB_DATA_ADVANCE2.set_transfer_information(dma.DMA_TD_MODE)
CB_DATA_ADVANCE2.set_source_addr(dma_data.start_address)
CB_DATA_ADVANCE2.set_destination_addr(cb_data_advance2_src_addr)
CB_DATA_ADVANCE2.set_transfer_length_stride(4, 2)
CB_DATA_ADVANCE2.set_stride(src_stride2, dest_stride2)
CB_DATA_ADVANCE2.set_next_cb(CB_DATA_SET_CLR.addr)

CB_DATA_SET_CLR.set_transfer_information(dma.DMA_NO_WIDE_BURSTS | dma.DMA_DEST_INC | dma.DMA_SRC_INC | DMA_WAITS)
CB_DATA_SET_CLR.set_transfer_length(20)
CB_DATA_SET_CLR.set_source_addr(MS_BASE_BUS + MS_MBOX_REG_OFFSET)
CB_DATA_SET_CLR.set_destination_addr(gpio.GPIO_BASE_BUS + gpio.GPSET0_REG_OFFSET)
CB_DATA_SET_CLR.set_next_cb(CB_DATA_WAIT1.addr)

CB_DATA_WAIT1.set_transfer_information(DMA_FLAGS_PWM)
CB_DATA_WAIT1.set_destination_addr(pwm.PWM_BASE_BUS + pwm.PWM_FIFO)
CB_DATA_WAIT1.set_next_cb(CB_DATA_CLR.addr)

CB_DATA_CLR.set_transfer_information(dma.DMA_NO_WIDE_BURSTS | dma.DMA_SRC_INC | dma.DMA_DEST_INC)
CB_DATA_CLR.set_transfer_length(8)
CB_DATA_CLR.set_source_addr(MS_BASE_BUS + MS_MBOX_REG_OFFSET)
CB_DATA_CLR.set_destination_addr(gpio.GPIO_BASE_BUS + gpio.GPCLR0_REG_OFFSET)
CB_DATA_CLR.set_next_cb(CB_DATA_WAIT2.addr)

CB_DATA_WAIT2.set_transfer_information(DMA_FLAGS_PWM)
CB_DATA_WAIT2.set_destination_addr(pwm.PWM_BASE_BUS + pwm.PWM_FIFO)

CB_PAUSE.set_transfer_length(4)
CB_PAUSE.write_word_to_source_data(0, CB_IDLE_WAIT.addr)
CB_PAUSE.set_destination_addr(CB_IDLE_CLR.addr + 0x14)
CB_PAUSE.set_next_cb(CB_IDLE_CLR.addr)

dma_data.set_cb_addrs(CB_DATA_ADVANCE.addr, CB_PAUSE.addr)

#############
# Start DMA #
#############
pwm.configure_and_start_pwm(DMA_CH, PWM_CLK_SRC, PWM_CLK_DIV_INT, PWM_CLK_DIV_FRAC, PWM_CYCLES)
gpio.set_pin_fnc_to_output(GPIO_INFO_PIN15)
gpio.set_pin_fnc_to_output(GPIO_INFO_PIN18)
dma.activate_channel_with_cb(DMA_CH, CB_IDLE_WAIT.addr)

start = time.time()
while time.time() - start < PLAY_SECONDS:
    CB_IDLE_CLR.set_next_cb(CB_DATA_ADVANCE.addr)
    time.sleep(.01)

pwm.stop_pwm(DMA_CH, PWM_CLK_SRC)
