import ctypes

import mmap

import app.memory_utils as mu


class ControlBlock:
    def __init__(self):
        self.data_mem = None
        self.cb_mem = mu.ctypes_alloc_aligned(32, 32)
        self.cb_addr = mu.virtual_to_physical_addr(ctypes.addressof(self.cb_mem)).p_addr

    def set_transfer_information(self, transfer_information):
        mu.write_word_to_byte_array(self.cb_mem, 0x0, transfer_information)

    def set_destination_addr(self, dest_addr):
        mu.write_word_to_byte_array(self.cb_mem, 0x8, dest_addr)

    def init_source_data(self, size):
        self.data_mem = mu.ctypes_alloc_aligned(size, 32)
        data_addr = mu.virtual_to_physical_addr(ctypes.addressof(self.data_mem)).p_addr
        mu.write_word_to_byte_array(self.cb_mem, 0x4, data_addr)
        mu.write_word_to_byte_array(self.cb_mem, 0xC, size)

    def set_source_data(self, data_byte_arr):
        data_len = len(data_byte_arr)
        self.data_mem = mu.ctypes_alloc_aligned(data_len, 32)
        data_addr = mu.virtual_to_physical_addr(ctypes.addressof(self.data_mem)).p_addr
        mu.write_word_to_byte_array(self.cb_mem, 0x4, data_addr)
        mu.write_word_to_byte_array(self.cb_mem, 0xC, data_len)

    def set_stride(self, stride):
        mu.write_word_to_byte_array(self.cb_mem, 0x10, stride)

    def set_next_cb(self, next_cb_addr):
        mu.write_word_to_byte_array(self.cb_mem, 0x14, next_cb_addr)


PERIPHERAL_BASE_PHYS = 0x20000000
DMA_OFFSET = 0x7000
DMA_BASE = PERIPHERAL_BASE_PHYS + DMA_OFFSET

MMAP_FLAGS = mmap.MAP_SHARED
MMAP_PROT = mmap.PROT_READ | mmap.PROT_WRITE


def activate_channel_with_cb(channel, cb_addr):
    if channel < 0 | channel > 14:
        raise Exception("Invalid channel index: {}".format(channel))

    with open("/dev/mem", "r+b", buffering=0) as f:
        with mmap.mmap(f.fileno(), 4096, MMAP_FLAGS, MMAP_PROT, offset=DMA_BASE) as dma_mem:
            # Reset channel:
            mu.write_word_to_byte_array(dma_mem, 0x100 * channel + 0x0, 0b1 << 31)
            # Write address of CB to CB_ADDR register:
            mu.write_word_to_byte_array(dma_mem, 0x100 * channel + 0x4, cb_addr)
            # Activate channel:
            mu.write_word_to_byte_array(dma_mem, 0x100 * channel + 0x0, 0b1)


def build_linked_cb_list(length):
    cb_list = []

    i = 0
    while i < length:
        new_cb = ControlBlock()
        cb_list.append(new_cb)

        if i > 0:
            cb_list[i-1].set_next_cb(new_cb.cb_addr)

        i += 1
