#!/usr/bin/env python3
import ctypes
import os
import mmap

HIGH_WAITS_0 = 1
HIGH_WAITS_1 = 1
LOW_WAITS = 1


# size and alignment are in bytes
def ctypes_alloc_aligned(size, alignment):
    # Account for a potential shift of up to (alignment-1)
    buf_size = size + alignment - 1
    # Allocate the memory as a Python byte array
    raw_memory = bytearray(buf_size)

    # c_char is exactly one byte. In Python, multiplying a type T by N creates a new type that is an Array of N Ts.
    ctypes_raw_type = ctypes.c_char * buf_size
    # Instantiate my Array<c_char> that sits in raw_memory. This is only in order to get the address of raw_memory via ctypes
    ctypes_raw_memory = ctypes_raw_type.from_buffer(raw_memory)

    raw_address = ctypes.addressof(ctypes_raw_memory)
    offset = alignment - raw_address % alignment

    ctypes_aligned_type = ctypes.c_char * (buf_size - offset)
    ctypes_aligned_memory = ctypes_aligned_type.from_buffer(raw_memory, offset)

    return ctypes_aligned_memory


def add_byte_to_memory(byte, memory, p):
    i = 0
    while i < 8:
        if(((byte >> i) & 1) == 1):
            p = build_gpio_one(memory, p)
        else:
            p = build_gpio_zero(memory, p)
        i += 1
    return p


def build_gpio_zero(memory, p):
    memory[p+1] = b'\x04'  # Set pin 18
    p += 16*(HIGH_WAITS_0 + 1)  # Wait
    memory[p+13] = b'\x04'  # Clear pin 18
    p += 16*(LOW_WAITS + 1)
    return p


def build_gpio_one(memory, p):
    memory[p+1] = b'\x04'  # Set pin 18
    p += 16*(HIGH_WAITS_1 + 1)  # Wait
    memory[p+13] = b'\x04'  # Clear pin 18
    p += 16*(LOW_WAITS + 1)
    return p


def print_bytes(memory):
    byte_length = len(memory)
    i = 0
    while i < byte_length:
        byte = memory[i]
        print(byte)
        i += 1
    return


def write_bits_to_word(word, value, high_bit, low_bit):
    if word is None:
        word = int(0)
    p = low_bit
    while p <= high_bit:
        word &= ~(1 << p)
        p += 1
    return word | (value << low_bit)


def write_word_to_cb_memory(word, cb_memory, cb_word):
    bytes = word.to_bytes(4, byteorder='big')
    i = 0
    while i < 4:
        cb_memory[i + 4 * cb_word] = bytes[i]
        i += 1
    return cb_memory

#################################
## Add color bytes into memory ##
#################################


bytes = b'\x04\xff\xf4'
data_mem = ctypes_alloc_aligned(2048, 16)
pointer = add_byte_to_memory(bytes[0], data_mem, 0)
pointer = add_byte_to_memory(bytes[1], data_mem, pointer)
pointer = add_byte_to_memory(bytes[2], data_mem, pointer)
# print_bytes(data_mem)

data_addr = ctypes.addressof(data_mem)

##################################
## Build DMA Control Block (CB) ##
##################################

# Define all the fields of the CB.
# The number(s) in the comment after each field
# specify the bit(s) of the CB the field should be written to

# CB Word 0:
NO_WIDE_BURSTS = 0b1  # 26
WAITS = 0b11111  # 25:21
PERMAP = 0b0  # 20:16
BURST_LENGTH = 0b0  # 15:12
SRC_IGNORE = 0b0  # 11
SRC_DREQ = 0b0  # 10
SRC_WIDTH = 0b1  # 9
SRC_INC = 0b1  # 8
DEST_IGNORE = 0b0  # 7
DEST_DREQ = 0b0  # 6
DEST_WIDTH = 0b1  # 5
DEST_INC = 0b0  # 4
WAIT_RESP = 0b0  # 3
TDMODE = 0b0  # 1
INTEN = 0b0  # 0

cb_word_0 = write_bits_to_word(None, NO_WIDE_BURSTS, 26, 26)
cb_word_0 = write_bits_to_word(cb_word_0, WAITS, 25, 21)
cb_word_0 = write_bits_to_word(cb_word_0, PERMAP, 20, 16)
cb_word_0 = write_bits_to_word(cb_word_0, BURST_LENGTH, 15, 12)
cb_word_0 = write_bits_to_word(cb_word_0, SRC_IGNORE, 11, 11)
cb_word_0 = write_bits_to_word(cb_word_0, SRC_DREQ, 10, 10)
cb_word_0 = write_bits_to_word(cb_word_0, SRC_WIDTH, 9, 9)
cb_word_0 = write_bits_to_word(cb_word_0, SRC_INC, 8, 8)
cb_word_0 = write_bits_to_word(cb_word_0, DEST_IGNORE, 7, 7)
cb_word_0 = write_bits_to_word(cb_word_0, DEST_DREQ, 6, 6)
cb_word_0 = write_bits_to_word(cb_word_0, DEST_WIDTH, 5, 5)
cb_word_0 = write_bits_to_word(cb_word_0, DEST_INC, 4, 4)
cb_word_0 = write_bits_to_word(cb_word_0, WAIT_RESP, 3, 3)
cb_word_0 = write_bits_to_word(cb_word_0, TDMODE, 1, 1)
cb_word_0 = write_bits_to_word(cb_word_0, INTEN, 0, 0)

# CB Word 1:
cb_word_1 = write_bits_to_word(None, data_addr, 31, 0)

# CB Word 2:
gpio_bus_addr = 0x7E20001C
cb_word_2 = write_bits_to_word(None, gpio_bus_addr, 31, 0)

# CB Word 3:
txfr_len = 2048 # later on, this should be automatically calculated based on how many LEDs we want to send data for
cb_word_3 = write_bits_to_word(None, txfr_len, 29, 0)

# CB Word 4:
cb_word_4 = write_bits_to_word(None, 0, 31, 0)

# CB Word 5:
cb_word_5 = write_bits_to_word(None, 0, 31, 0)

# CB is 32 bytes long (8 words), though only 24 bytes (6 words) are used
# CB address must be 256-bit (32-byte) aligned
cb_mem = ctypes_alloc_aligned(32, 32)

write_word_to_cb_memory(cb_word_0, cb_mem, 0)
write_word_to_cb_memory(cb_word_1, cb_mem, 1)
write_word_to_cb_memory(cb_word_2, cb_mem, 2)
write_word_to_cb_memory(cb_word_3, cb_mem, 3)
write_word_to_cb_memory(cb_word_4, cb_mem, 4)
write_word_to_cb_memory(cb_word_5, cb_mem, 5)

CB_ADDR = ctypes.addressof(cb_mem)

# Make sure the bottom 5 bits are 0:
# print("{0:b}".format(CB_ADDR))

# Open /dev/mem (peripheral memory) as file and get a pointer to its
# address in the program's virtual address space:

# We provide an offset, so that we're mapped directly to DMA memory (no peripheral base)
# Peripheral base (bus) is 0x7E000000, and DMA Channel 0 base is 0x7E007000
# Thus the offset is 0x7000 from the start of /dev/mem file
dma_offset = 0x7000
file = os.open("/dev/mem", os.O_RDWR | os.O_SYNC)

# TODO: This is missing the "Access" param. how do I not specify it?
dma_mem = mmap.mmap(file, 4096, mmap.MAP_SHARED, mmap.PROT_READ | mmap.PROT_WRITE, offset = dma_offset)

# Write CB_ADDR to register 2 of dma_mem (Channel 0 of DMA)
cb_addr_bytes = CB_ADDR.to_bytes(4, byteorder='big')
dma_mem[4:8] = cb_addr_bytes

# Set the active bit of DMA Channel 0
dma_mem[3] = 0x1