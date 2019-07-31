#!/usr/bin/env python3
import ctypes
import time

import mmap

import app.memory_utils as mu

HIGH_WAITS_0 = 1
HIGH_WAITS_1 = 1
LOW_WAITS = 1

def write_word_to_byte_array(byte_array, address, word):
    byte_array[address: address + 4] = word.to_bytes(4, byteorder='little')
    return


def print_dma_debug_info(dma_memory):
    debug_register_offset = 0x20
    i = 0
    while i < 15:
        start = i * 0x100 + debug_register_offset
        arr = dma_memory[start: start + 4]
        rev = arr[::-1]
        print('CH' + str(i) + ':\t' + ':'.join(format(x, '08b') for x in rev))
        i += 1
    return


def print_dma_enabled_state(dma_memory):
    enable_offset = 0xFF0
    arr = dma_memory[enable_offset: enable_offset + 4]
    rev = arr[::-1]
    print(':'.join(format(x, '08b') for x in rev))
    return


########################
## Build data to send ##
########################

data_len = 64  # bytes
data_mem = mu.ctypes_alloc_aligned(data_len, 32)
# write_word_to_byte_array(data_mem, 0x4, 0b001 << 24)  # set pin 18
write_word_to_byte_array(data_mem, 0x1C, 0b1 << 18)  # set pin 18
# write_word_to_byte_array(data_mem, 0x28, 0b1 << 18) # clear pin 18
data_addr = ctypes.addressof(data_mem)

##################################
## Build DMA Control Block (CB) ##
##################################

# CB is 32 bytes long (8 words), though only 24 bytes (6 words) are used
# CB address must be 256-bit (32-byte) aligned
cb_mem = mu.ctypes_alloc_aligned(32, 32)
cb_addr = ctypes.addressof(cb_mem)

# Define all the fields of the CB.

# CB Word 0:
# NO_WIDE_BURSTS = 0b1 << 26  # 26
# WAITS = 0b11111 << 21 # 25:21
# SRC_WIDTH = 0b1 << 9
SRC_INC = 0b1 << 8
# DEST_WIDTH = 0b1 << 5
DEST_INC = 0b1 << 4

write_word_to_byte_array(cb_mem, 0x0, SRC_INC | DEST_INC)

# CB Word 1 (SRC_ADDR):
write_word_to_byte_array(cb_mem, 0x4, data_addr)

# CB Word 2 (DEST_ADDR):
gpio_phys_addr = 0x20200000
write_word_to_byte_array(cb_mem, 0x8, gpio_phys_addr)

# CB Word 3 (TXFR_LEN):
txfr_len = data_len
write_word_to_byte_array(cb_mem, 0xC, txfr_len)

# CB Word 4 (STRIDE):
# Nothing to write, since we're not using 2D Stride

# CB Word 5 (NEXTCONBK):
# Nothing to write, since we're only sending one control block

##################
## Write to DMA ##
##################

# Open /dev/mem (peripheral memory) as file and get a pointer to its address in the program's virtual address space:
# We provide an offset, so that we're mapped directly to DMA memory


PERIPHERAL_BASE = 0x20000000  # Physical
DMA_OFFSET = 0x7000
DMA_BASE = PERIPHERAL_BASE + DMA_OFFSET

with open("/dev/mem", "r+b", buffering=0) as f:
    with mmap.mmap(f.fileno(), 4096, mmap.MAP_SHARED, mmap.PROT_READ | mmap.PROT_WRITE, offset=DMA_BASE) as dma_mem:
        # print_dma_enabled_state(dma_mem)
        write_word_to_byte_array(dma_mem, 0x4, cb_addr)
        time.sleep(.5)
        write_word_to_byte_array(dma_mem, 0x0, 0b1)
        time.sleep(.5)
