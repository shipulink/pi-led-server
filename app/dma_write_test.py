#!/usr/bin/env python3
import ctypes
import time

import mmap

import app.memory_utils as mu

LITTLE_ENDIAN = "little"
BIG_ENDIAN = "big"


# TODO: Move to memory_utils
def write_word_to_byte_array(byte_array, address, word, endianness):
    # print("word: " + hex(word))
    word_bytes = word.to_bytes(4, byteorder=endianness)
    # print("bytes: " + ''.join(format(x, '0x') for x in word_bytes))
    byte_array[address: address + 4] = word_bytes
    return


data_len = 8

#######################
## Build source data ##
#######################
src_mem = mu.ctypes_alloc_aligned(data_len, 32)
# src_mem[0:data_len] = b"Greetings world!"
# write_word_to_byte_array(src_mem, 0x0, 0xf0f0ffff, BIG_ENDIAN)
# write_word_to_byte_array(src_mem, 0x4, 0xffffffff, BIG_ENDIAN)
write_word_to_byte_array(src_mem, 0x4, 0x01000000, BIG_ENDIAN)
# write_word_to_byte_array(src_mem, 0x8, 0xf0f0ffff, BIG_ENDIAN)
# write_word_to_byte_array(src_mem, 0xC, 0xffffffff, BIG_ENDIAN)

src_addr_virtual = ctypes.addressof(src_mem)
src_addr_info = mu.virtual_to_physical_addr(src_addr_virtual)
src_addr = src_addr_info.p_addr

############################
## Build destination data ##
############################
dest_mem = mu.ctypes_alloc_aligned(data_len, 32)
dest_addr_virtual = ctypes.addressof(dest_mem)
dest_addr_info = mu.virtual_to_physical_addr(dest_addr_virtual)
dest_addr = dest_addr_info.p_addr

##################################
## Build DMA Control Block (CB) ##
##################################

cb_mem = mu.ctypes_alloc_aligned(32, 32)
cb_addr_virtual = ctypes.addressof(cb_mem)
cb_addr_info = mu.virtual_to_physical_addr(cb_addr_virtual)
cb_addr = cb_addr_info.p_addr

# CB Word 0 (SRC_ADDR):
SRC_INC = 0b1 << 8
DEST_INC = 0b1 << 4
write_word_to_byte_array(cb_mem, 0x0, SRC_INC | DEST_INC, LITTLE_ENDIAN)

# CB Word 1 (SRC_ADDR):
write_word_to_byte_array(cb_mem, 0x4, src_addr, LITTLE_ENDIAN)

# CB Word 2 (DEST_ADDR) - physical GPIO memory address:
write_word_to_byte_array(cb_mem, 0x8, dest_addr, LITTLE_ENDIAN)

# CB Word 3 (TXFR_LEN):
write_word_to_byte_array(cb_mem, 0xC, data_len, LITTLE_ENDIAN)

##################
## Write to DMA ##
##################

PERIPHERAL_BASE = 0x20000000  # Physical
DMA_OFFSET = 0x7000
DMA_BASE = PERIPHERAL_BASE + DMA_OFFSET

with open("/dev/mem", "r+b", buffering=0) as f:
    with mmap.mmap(f.fileno(), 4096, mmap.MAP_SHARED, mmap.PROT_READ | mmap.PROT_WRITE, offset=DMA_BASE) as dma_mem:
        write_word_to_byte_array(dma_mem, 0x4, cb_addr, LITTLE_ENDIAN)
        time.sleep(.5)
        write_word_to_byte_array(dma_mem, 0x0, 0b1, LITTLE_ENDIAN)
        time.sleep(.5)

with open("/dev/mem", "r+b", buffering=0) as f:
    with mmap.mmap(f.fileno(), 4096, mmap.MAP_SHARED, mmap.PROT_READ | mmap.PROT_WRITE,
                   offset=dest_addr_info.frame_start) as m:
        s = dest_addr_info.offset
        # print(m[s:s+data_len].decode('utf8'))
        print(':'.join(format(x, '08b') for x in m[s:s + data_len]))
