import array
import time

import app.dma as dma
import app.led_frame_data as fd
import app.memory_utils as mu

PLAY_SECONDS = 5
DMA_CH = 2

# GPIO addresses
GPIO_BASE = 0x7E200000
GPFSEL1 = GPIO_BASE + 0x4
GPSET0 = GPIO_BASE + 0x1C
GPCLR0 = GPIO_BASE + 0x28

# DMA constants
DMA_TD_MODE = 1 << 1
DMA_WAIT_RESP = 1 << 3
DMA_DEST_INC = 1 << 4
DMA_SRC_INC = 1 << 8
DMA_SRC_IGNORE = 1 << 11
DMA_WAITS = 31 << 21
DMA_WAITS_ZERO = 12 << 21
DMA_WAITS_ONE = 20 << 21
DMA_NO_WIDE_BURSTS = 1 << 26

DMA_FLAGS_DATA = DMA_NO_WIDE_BURSTS | DMA_WAIT_RESP
DMA_FLAGS_WAIT = DMA_NO_WIDE_BURSTS | DMA_SRC_IGNORE | DMA_WAIT_RESP

# Build control array from incoming bytes
ints = [
    0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00
    # 0x00, 0x11, 0x00, 0x11, 0x00, 0x00, 0x00, 0x00, 0x11, 0x00, 0x11, 0x00, 0x11, 0x00, 0x00, 0x00, 0x00, 0x11
    # 0x00, 0xFF, 0x00, 0xFF, 0x00, 0x00, 0x00, 0x00, 0xFF, 0x00, 0xFF, 0x00, 0xFF, 0x00, 0x00, 0x00, 0x00, 0xFF
    # 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF
]
byte_arr = array.array("B", ints)

dma_data = fd.LedDmaFrameData(int(len(byte_arr) / 3))

# Allocate enough memory for all the CBs.
shared_mem = mu.create_phys_contig_int_view(256)

# CBs that don't need dedicated space for source data
CB_IDLE_WAIT = dma.ControlBlock3(shared_mem, 0)
CB_ONE_WAIT2 = dma.ControlBlock3(shared_mem, 8)
CB_DATA_WAIT2 = dma.ControlBlock3(shared_mem, 16)
CB_DATA_WAIT3 = dma.ControlBlock3(shared_mem, 24)
CB_DATA_WAIT4 = dma.ControlBlock3(shared_mem, 32)
CB_ONE_WAIT1 = dma.ControlBlock3(shared_mem, 40)
CB_UPD = dma.ControlBlock3(shared_mem, 48)  # Needs stride. Updates its own src addr and CB_DATA_WAIT's next CB addr

# CBs that need dedicated space for data
CB_IDLE_CLR = dma.ControlBlock3(shared_mem, 80)
CB_DATA_CLR = dma.ControlBlock3(shared_mem, 96)
CB_STOP = dma.ControlBlock3(shared_mem, 112)
CB_ZERO_SET = dma.ControlBlock3(shared_mem, 128)
CB_ONE_SET = dma.ControlBlock3(shared_mem, 144)

# Configure idle loop
CB_IDLE_WAIT.set_transfer_information(DMA_FLAGS_WAIT | DMA_WAITS)
CB_IDLE_WAIT.set_destination_addr(GPCLR0)
CB_IDLE_WAIT.set_next_cb(CB_IDLE_CLR.addr)

CB_IDLE_CLR.set_transfer_information(DMA_FLAGS_DATA)
CB_IDLE_CLR.write_word_to_source_data(0x0, 1 << 18)  # pin 18
CB_IDLE_CLR.set_destination_addr(GPCLR0)
CB_IDLE_CLR.set_next_cb(CB_IDLE_WAIT.addr)

# Configure data loop

CB_DATA_CLR.set_transfer_information(DMA_FLAGS_DATA)
CB_DATA_CLR.write_word_to_source_data(0, 1 << 18)  # pin 18
CB_DATA_CLR.set_destination_addr(GPCLR0)
CB_DATA_CLR.set_next_cb(CB_UPD.addr)

src_stride = int(dma_data.view_len / 2 * 4)
dest_stride = CB_DATA_WAIT2.addr + 0x14 - (CB_UPD.addr + 0x4)
CB_UPD.set_transfer_information(DMA_FLAGS_DATA | DMA_TD_MODE)
CB_UPD.set_source_addr(dma_data.base_addrs[0])
CB_UPD.set_destination_addr(CB_UPD.addr + 0x4)
CB_UPD.set_transfer_length_stride(4, 2)
CB_UPD.set_stride(src_stride, dest_stride)
CB_UPD.set_next_cb(CB_DATA_WAIT2.addr)

CB_DATA_WAIT2.set_transfer_information(DMA_FLAGS_WAIT | DMA_WAITS)
CB_DATA_WAIT2.set_destination_addr(GPCLR0)

CB_STOP.set_transfer_information(DMA_FLAGS_DATA)
CB_STOP.write_word_to_source_data(0, CB_IDLE_WAIT.addr)
CB_STOP.set_destination_addr(CB_IDLE_CLR.addr + 0x14)
CB_STOP.set_next_cb(CB_IDLE_WAIT.addr)

CB_ZERO_SET.set_transfer_information(DMA_FLAGS_DATA | DMA_WAITS_ZERO)
CB_ZERO_SET.init_source_data(8)
CB_ZERO_SET.write_word_to_source_data(1, 1 << 18)  # pin 18
CB_ZERO_SET.set_destination_addr(GPSET0)
CB_ZERO_SET.set_next_cb(CB_DATA_CLR.addr)

CB_ONE_SET.set_transfer_information(DMA_FLAGS_DATA)
CB_ONE_SET.write_word_to_source_data(0, 1 << 18)  # pin 18
CB_ONE_SET.set_destination_addr(GPSET0)
CB_ONE_SET.set_next_cb(CB_ONE_WAIT1.addr)

CB_ONE_WAIT1.set_transfer_information(DMA_FLAGS_WAIT | DMA_WAITS_ONE)
CB_ONE_WAIT1.set_destination_addr(GPCLR0)
CB_ONE_WAIT1.set_next_cb(CB_ONE_WAIT2.addr)

CB_ONE_WAIT2.set_transfer_information(DMA_FLAGS_WAIT | DMA_WAITS_ONE)
CB_ONE_WAIT2.set_destination_addr(GPCLR0)
CB_ONE_WAIT2.set_next_cb(CB_DATA_CLR.addr)

dma_data.set_cb_addrs(CB_ZERO_SET.addr, CB_ONE_SET.addr, CB_STOP.addr)
dma_data.populate_with_data(byte_arr)
# dma_data.print_debug_info()

#############
# Init GPIO #
#############
cb_gpio_conf = dma.ControlBlock()
cb_gpio_conf.init_source_data(4)
cb_gpio_conf.write_word_to_source_data(0x0, 1 << 24)
cb_gpio_conf.set_transfer_information(DMA_WAIT_RESP)
cb_gpio_conf.set_destination_addr(GPFSEL1)
dma.activate_channel_with_cb(DMA_CH, cb_gpio_conf.addr)
time.sleep(0.1)

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
