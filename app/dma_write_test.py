#!/usr/bin/env python3
import ctypes

import mmap

import app.dma as dma
import app.memory_utils as mu

MMAP_FLAGS = mmap.MAP_SHARED
MMAP_PROT = mmap.PROT_READ | mmap.PROT_WRITE

data = mu.ctypes_alloc_aligned(128, 32)
data_info = mu.virtual_to_physical_addr(ctypes.addressof(data))
data_addr = data_info.p_addr

cb = dma.ControlBlock()
cb.init_source_data(64)
cb.write_word_to_source_data(0x0, 0xFFEEDDCC)
cb.write_word_to_source_data(0x10, 0xAABBCCDD)
cb.write_word_to_source_data(0x20, 0x11223344)
cb.write_word_to_source_data(0x30, 0xAABBCCDD)
cb.set_transfer_information(1 << 26 | 0b11111 << 21 | 1 << 8 | 1 << 4 | 1 << 1)
cb.set_transfer_length_stride(16, 3)
cb.set_stride(0, -16)
cb.set_destination_addr(data_addr)

dma.activate_channel_with_cb(0, cb.addr)

with open("/dev/mem", "r+b", buffering=0) as f:
    with mmap.mmap(f.fileno(), 4096, MMAP_FLAGS, MMAP_PROT, offset=data_info.frame_start) as m:
        s = data_info.offset
        print(':'.join(format(x, '02x') for x in m[s:s + 16][::-1]))
        print(':'.join(format(x, '02x') for x in m[s + 16:s + 32][::-1]))
