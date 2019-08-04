#!/usr/bin/env python3
import ctypes

import mmap

import app.memory_utils as mu

LITTLE_ENDIAN = "little"
BIG_ENDIAN = "big"

PERIPHERAL_BASE_PHYS = 0x20000000
PERIPHERAL_BASE_BUS = 0x7E000000

DMA_OFFSET = 0x7000
DMA_BASE = PERIPHERAL_BASE_PHYS + DMA_OFFSET

GPIO_OFFSET = 0x200000
GPIO_BASE_PHYS = PERIPHERAL_BASE_PHYS + GPIO_OFFSET
GPIO_BASE_BUS = PERIPHERAL_BASE_BUS + GPIO_OFFSET

SRC_INC = 1 << 8
DEST_INC = 1 << 4


def write_word_to_byte_array(byte_array, address, word, endianness):
    byte_array[address: address + 4] = word.to_bytes(4, byteorder=endianness)
    return


data_len = 4  # bytes

src_mem = mu.ctypes_alloc_aligned(data_len, 256)
src_addr_virtual = ctypes.addressof(src_mem)
src_addr_info = mu.virtual_to_physical_addr(src_addr_virtual)
src_addr = src_addr_info.p_addr
write_word_to_byte_array(src_mem, 0x0, 1 << 24, LITTLE_ENDIAN)
# write_word_to_byte_array(src_mem, 0x0, 0x00000000, LITTLE_ENDIAN)
# write_word_to_byte_array(src_mem, 0x4, 0xffff, LITTLE_ENDIAN)

cb_mem = mu.ctypes_alloc_aligned(32, 256)
cb_addr_virtual = ctypes.addressof(cb_mem)
cb_addr = mu.virtual_to_physical_addr(cb_addr_virtual).p_addr

# CB Word 0 (transfer settings):
write_word_to_byte_array(cb_mem, 0x0, 1 << 26, LITTLE_ENDIAN)
write_word_to_byte_array(cb_mem, 0x4, src_addr, LITTLE_ENDIAN)  # CB WOrd 1 (source address)
write_word_to_byte_array(cb_mem, 0x8, GPIO_BASE_BUS + 0x4, LITTLE_ENDIAN)  # CB Word 2 (destination address)
write_word_to_byte_array(cb_mem, 0xC, data_len, LITTLE_ENDIAN)  # CB Word 3 (transfer length)

with open("/dev/mem", "r+b", buffering=0) as f:
    with mmap.mmap(f.fileno(), 4096, mmap.MAP_SHARED, mmap.PROT_READ | mmap.PROT_WRITE,
                   offset=GPIO_BASE_PHYS) as gpio_mem:
        print(':'.join(format(x, 'x') for x in gpio_mem[0x4:0x4+data_len]))

with open("/dev/mem", "r+b", buffering=0) as f:
    with mmap.mmap(f.fileno(), 4096, mmap.MAP_SHARED, mmap.PROT_READ | mmap.PROT_WRITE, offset=DMA_BASE) as dma_mem:
        write_word_to_byte_array(dma_mem, 0x0, 0b1 << 31, LITTLE_ENDIAN)  # Reset channel 0
        write_word_to_byte_array(dma_mem, 0x4, cb_addr, LITTLE_ENDIAN)  # Write address of CB to CB_ADDR register
        write_word_to_byte_array(dma_mem, 0x0, 0b1, LITTLE_ENDIAN)  # Activate channel 0

with open("/dev/mem", "r+b", buffering=0) as f:
    with mmap.mmap(f.fileno(), 4096, mmap.MAP_SHARED, mmap.PROT_READ | mmap.PROT_WRITE,
                   offset=GPIO_BASE_PHYS) as gpio_mem:
        print(':'.join(format(x, 'x') for x in gpio_mem[0x4:0x4+data_len]))
