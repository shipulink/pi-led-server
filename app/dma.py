import ctypes

import mmap

import app.memory_utils as mu


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


# DMA addresses and offsets:
DMA_BASE = 0x20007000
DMA_CS = 0x0
DMA_CB_AD = 0x4
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

MMAP_FLAGS = mmap.MAP_SHARED
MMAP_PROT = mmap.PROT_READ | mmap.PROT_WRITE


def activate_channel_with_cb(channel, cb_addr):
    if channel < 0 | channel > 14:
        raise Exception("Invalid channel index: {}".format(channel))

    with open("/dev/mem", "r+b", buffering=0) as f:
        with mmap.mmap(f.fileno(), 4096, MMAP_FLAGS, MMAP_PROT, offset=DMA_BASE) as dma_mem:
            mu.write_word_to_byte_array(dma_mem, 0x100 * channel + DMA_CS, DMA_RESET)
            mu.write_word_to_byte_array(dma_mem, 0x100 * channel + DMA_CS, DMA_INT | DMA_END)
            mu.write_word_to_byte_array(dma_mem, 0x100 * channel + DMA_DEBUG, DMA_DEBUG_CLR_ERRORS)
            mu.write_word_to_byte_array(dma_mem, 0x100 * channel + DMA_CS,
                                        DMA_WAIT_FOR_OUTSTANDING_WRITES | DMA_PANIC_PRIORITY | DMA_PRIORITY)
            mu.write_word_to_byte_array(dma_mem, 0x100 * channel + DMA_CB_AD, cb_addr)
            mu.write_word_to_byte_array(dma_mem, 0x100 * channel + DMA_CS, DMA_ACTIVE)


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
