import ctypes
import mmap
import time

import app.memory_utils as mu

# DMA addresses and offsets:
DMA_BASE_BUS = 0x7E007000
DMA_BASE = 0x20007000
DMA_BASE_CH15 = 0x20E05000
DMA_GLOBAL_ENABLE = 0xFF0
DMA_CS = 0x0
DMA_CB_AD = 0x4
DMA_TI = 0x8
DMA_DEBUG = 0x20

# DMA constants
DMA_RESET = 1 << 31
DMA_INT = 1 << 2
DMA_END = 1 << 1
DMA_WAIT_FOR_OUTSTANDING_WRITES = 1 << 28
DMA_PANIC_PRIORITY = 8 << 20
DMA_PRIORITY = 8 << 16
DMA_DEBUG_CLR_ERRORS = 0b111  # Clear Read Error, FIFO Error, Read Last Not Set Error
DMA_ACTIVE = 1

DMA_TD_MODE = 1 << 1
DMA_WAIT_RESP = 1 << 3
DMA_DEST_INC = 1 << 4
DMA_DEST_WIDTH = 1 << 5
DMA_DEST_DREQ = 1 << 6
DMA_DEST_IGNORE = 1 << 7
DMA_SRC_INC = 1 << 8
DMA_SRC_WIDTH = 1 << 9
DMA_SRC_IGNORE = 1 << 11
DMA_WAITS = 31 << 21
DMA_NO_WIDE_BURSTS = 1 << 26
DMA_PERMAP = 5 << 16  # 5 = PWM, 2 = PCM


class ControlBlock:
    def __init__(self):
        self.data_mem = None
        self.cb_mem = mu.ctypes_alloc_aligned(32, 32)
        self.addr = mu.virtual_to_physical_addr(ctypes.addressof(self.cb_mem)).p_addr

    def set_transfer_information(self, transfer_information):
        mu.write_word_to_byte_array(self.cb_mem, 0x0, transfer_information)

    def set_destination_addr(self, dest_addr):
        mu.write_word_to_byte_array(self.cb_mem, 0x8, dest_addr)

    def init_source_data(self, size):
        self.data_mem = mu.ctypes_alloc_aligned(size, 32)
        data_addr = mu.virtual_to_physical_addr(ctypes.addressof(self.data_mem)).p_addr
        mu.write_word_to_byte_array(self.cb_mem, 0x4, data_addr)
        mu.write_word_to_byte_array(self.cb_mem, 0xC, size)

    def write_word_to_source_data(self, offset, word):
        mu.write_word_to_byte_array(self.data_mem, offset, word)

    def set_source_data(self, data_byte_arr):
        data_len = len(data_byte_arr)
        self.data_mem = mu.ctypes_alloc_aligned(data_len, 32)
        data_addr = mu.virtual_to_physical_addr(ctypes.addressof(self.data_mem)).p_addr
        mu.write_word_to_byte_array(self.cb_mem, 0x4, data_addr)
        mu.write_word_to_byte_array(self.cb_mem, 0xC, data_len)

    def set_transfer_length_stride(self, x, y):
        mu.write_word_to_byte_array(self.cb_mem, 0xC, x | (y - 1) << 16)

    def set_stride(self, src, dest):
        if src < 0:
            src = src & 0xFFFF

        if dest < 0:
            dest = dest & 0xFFFF

        mu.write_word_to_byte_array(self.cb_mem, 0x10, src | dest << 16)

    def set_next_cb(self, next_cb_addr):
        mu.write_word_to_byte_array(self.cb_mem, 0x14, next_cb_addr)


class ControlBlock2:
    CB_TI = 0x0
    CB_SRC_ADDR = 0x4
    CB_DEST_ADDR = 0x8
    CB_TXFR_LEN = 0xC
    CB_STRIDE = 0x10
    CB_NEXT = 0x14

    DATA_OFFSET = 0x20

    def __init__(self, shared_mem_view, offset):
        self.shared_mem = shared_mem_view
        mv_phys_addr = mu.get_mem_view_phys_addr_info(shared_mem_view).p_addr
        self.offset = offset + 32 - mv_phys_addr % 32
        self.addr = mv_phys_addr + self.offset
        self.data_addr = self.addr + self.DATA_OFFSET
        self.data_len = 4
        mu.write_word_to_byte_array(self.shared_mem, self.offset + self.CB_SRC_ADDR, self.data_addr)
        mu.write_word_to_byte_array(self.shared_mem, self.offset + self.CB_TXFR_LEN, self.data_len)

    def set_transfer_information(self, transfer_information):
        mu.write_word_to_byte_array(self.shared_mem, self.offset + self.CB_TI, transfer_information)

    def set_destination_addr(self, dest_addr):
        mu.write_word_to_byte_array(self.shared_mem, self.offset + self.CB_DEST_ADDR, dest_addr)

    def set_source_addr(self, src_addr):
        mu.write_word_to_byte_array(self.shared_mem, self.offset + self.CB_SRC_ADDR, src_addr)

    # size is in bytes
    def init_source_data(self, size):
        self.data_len = size
        mu.write_word_to_byte_array(self.shared_mem, self.offset + self.CB_TXFR_LEN, self.data_len)

    def write_word_to_source_data(self, offset, word):
        mu.write_word_to_byte_array(self.shared_mem, self.offset + self.DATA_OFFSET + offset, word)

    # x = transfer length in bytes
    # y = number of transfers
    def set_transfer_length_stride(self, x, y):
        self.data_len = x * y
        mu.write_word_to_byte_array(self.shared_mem, self.offset + self.CB_TXFR_LEN, x | (y - 1) << 16)

    def set_stride(self, src, dest):
        if src < 0:
            src = src & 0xFFFF

        if dest < 0:
            dest = dest & 0xFFFF

        mu.write_word_to_byte_array(self.shared_mem, self.offset + self.CB_STRIDE, src | dest << 16)

    def set_next_cb(self, next_cb_addr):
        mu.write_word_to_byte_array(self.shared_mem, self.offset + self.CB_NEXT, next_cb_addr)


class ControlBlock3:
    CB_TI = 0
    CB_SRC_ADDR = 1
    CB_DEST_ADDR = 2
    CB_TXFR_LEN = 3
    CB_STRIDE = 4
    CB_NEXT = 5

    DATA_OFFSET = 0x20

    def __init__(self, shared_mem_view, offset):
        self.shared_mem = shared_mem_view
        mv_phys_addr = mu.get_mem_view_phys_addr_info(self.shared_mem).p_addr
        self.offset = int(((offset * 4) + 32 - mv_phys_addr % 32) / 4)
        self.addr = mv_phys_addr + self.offset * 4
        self.data_addr = self.addr + self.DATA_OFFSET
        self.data_len = 4
        self.shared_mem[self.offset + self.CB_SRC_ADDR] = self.data_addr
        self.shared_mem[self.offset + self.CB_TXFR_LEN] = self.data_len

    def set_transfer_information(self, transfer_information):
        self.shared_mem[self.offset + self.CB_TI] = transfer_information

    def set_destination_addr(self, dest_addr):
        self.shared_mem[self.offset + self.CB_DEST_ADDR] = dest_addr

    def set_source_addr(self, src_addr):
        self.shared_mem[self.offset + self.CB_SRC_ADDR] = src_addr

    # size is in bytes
    def init_source_data(self, size):
        self.data_len = size
        self.shared_mem[self.offset + self.CB_TXFR_LEN] = self.data_len

    def write_word_to_source_data(self, offset, word):
        self.shared_mem[self.offset + int(self.DATA_OFFSET / 4) + offset] = word

    def set_transfer_length(self, length):
        self.data_len = length
        self.shared_mem[self.offset + self.CB_TXFR_LEN] = length

    # x = transfer length in bytes
    # y = number of transfers
    def set_transfer_length_stride(self, x, y):
        self.data_len = x * y
        self.shared_mem[self.offset + self.CB_TXFR_LEN] = x | (y - 1) << 16

    def set_stride(self, src, dest):
        if src < 0:
            src = src & 0xFFFF

        if dest < 0:
            dest = dest & 0xFFFF

        self.shared_mem[self.offset + self.CB_STRIDE] = src | dest << 16

    def set_next_cb(self, next_cb_addr):
        self.shared_mem[self.offset + self.CB_NEXT] = next_cb_addr


def activate_channel_with_cb(channel, cb_addr, do_start=True):
    if channel < 0 | channel > 15:
        raise Exception("Invalid channel index: {}".format(channel))

    if channel < 15:
        ch_base = DMA_BASE
    else:
        ch_base = DMA_BASE_CH15

    ch_dma_cs = 0x100 * channel + DMA_CS
    ch_dma_debug = 0x100 * channel + DMA_DEBUG
    ch_dma_cb_ad = 0x100 * channel + DMA_CB_AD

    with open("/dev/mem", "r+b", buffering=0) as f:
        with mmap.mmap(f.fileno(), 4096, mu.MMAP_FLAGS, mu.MMAP_PROT, offset=ch_base) as dma_mem:
            mu.write_word_to_byte_array(dma_mem, ch_dma_cs, DMA_RESET)
            mu.write_word_to_byte_array(dma_mem, ch_dma_cs, DMA_INT | DMA_END)
            mu.write_word_to_byte_array(dma_mem, ch_dma_debug, DMA_DEBUG_CLR_ERRORS)
            mu.write_word_to_byte_array(dma_mem, ch_dma_cs,
                                        DMA_WAIT_FOR_OUTSTANDING_WRITES |
                                        DMA_PANIC_PRIORITY |
                                        DMA_PRIORITY)
            mu.write_word_to_byte_array(dma_mem, ch_dma_cb_ad, cb_addr)
            if do_start:
                mu.write_word_to_byte_array(dma_mem, ch_dma_cs, DMA_ACTIVE)

    time.sleep(0.1)


def build_linked_cb_list(length):
    cb_list = []
    i = 0
    while i < length:
        new_cb = ControlBlock()
        cb_list.append(new_cb)
        if i > 0:
            cb_list[i - 1].set_next_cb(new_cb.addr)
        i += 1
    return cb_list
