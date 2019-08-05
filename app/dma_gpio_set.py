#!/usr/bin/env python3
import ctypes

import mmap

import app.memory_utils as mu

PERIPHERAL_BASE_PHYS = 0x20000000
PERIPHERAL_BASE_BUS = 0x7E000000
DMA_OFFSET = 0x7000
DMA_BASE = PERIPHERAL_BASE_PHYS + DMA_OFFSET
GPIO_OFFSET = 0x200000
GPIO_BASE_PHYS = PERIPHERAL_BASE_PHYS + GPIO_OFFSET
GPIO_BASE_BUS = PERIPHERAL_BASE_BUS + GPIO_OFFSET

data_len = 4  # bytes

src_mem = mu.ctypes_alloc_aligned(data_len, 256)
src_addr_virtual = ctypes.addressof(src_mem)
src_addr_info = mu.virtual_to_physical_addr(src_addr_virtual)
src_addr = src_addr_info.p_addr
mu.write_word_to_byte_array(src_mem, 0x0, 1 << 24)

cb_mem = mu.ctypes_alloc_aligned(32, 256)
cb_addr_virtual = ctypes.addressof(cb_mem)
cb_addr = mu.virtual_to_physical_addr(cb_addr_virtual).p_addr

mu.write_word_to_byte_array(cb_mem, 0x0, 1 << 26)  # CB Word 0 (transfer settings):
mu.write_word_to_byte_array(cb_mem, 0x4, src_addr)  # CB WOrd 1 (source address)
mu.write_word_to_byte_array(cb_mem, 0x8, GPIO_BASE_BUS + 0x4)  # CB Word 2 (destination address)
mu.write_word_to_byte_array(cb_mem, 0xC, data_len)  # CB Word 3 (transfer length)

with open("/dev/mem", "r+b", buffering=0) as f:
    with mmap.mmap(f.fileno(), 4096, mmap.MAP_SHARED, mmap.PROT_READ | mmap.PROT_WRITE,
                   offset=GPIO_BASE_PHYS) as gpio_mem:
        print(':'.join(format(x, 'x') for x in gpio_mem[0x4:0x4 + data_len]))

with open("/dev/mem", "r+b", buffering=0) as f:
    with mmap.mmap(f.fileno(), 4096, mmap.MAP_SHARED, mmap.PROT_READ | mmap.PROT_WRITE, offset=DMA_BASE) as dma_mem:
        mu.write_word_to_byte_array(dma_mem, 0x0, 0b1 << 31)  # Reset channel 0
        mu.write_word_to_byte_array(dma_mem, 0x4, cb_addr)  # Write address of CB to CB_ADDR register
        mu.write_word_to_byte_array(dma_mem, 0x0, 0b1)  # Activate channel 0

with open("/dev/mem", "r+b", buffering=0) as f:
    with mmap.mmap(f.fileno(), 4096, mmap.MAP_SHARED, mmap.PROT_READ | mmap.PROT_WRITE,
                   offset=GPIO_BASE_PHYS) as gpio_mem:
        print(':'.join(format(x, 'x') for x in gpio_mem[0x4:0x4 + data_len]))
