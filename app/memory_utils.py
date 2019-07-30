import ctypes

import mmap
import os


class AddrInfo:
    def __init__(self):
        self.frame_start = None
        self.offset = None
        self.p_addr = None


def virtual_to_physical_addr(virtual_addr):
    # Data in pagemap is stored in 64-bit (8-byte) chunks. One per mapping.
    mapping_info_length = 8

    system_page_size = mmap.PAGESIZE
    with open("/proc/" + str(os.getpid()) + "/pagemap", "r+b") as pagemap_fd:
        pagemap_fd.seek(int(virtual_addr / system_page_size) * mapping_info_length)
        data_bytes = pagemap_fd.read(mapping_info_length)
        data = int.from_bytes(data_bytes, 'little')

        if ((data >> 63) & 1) == 1:
            addr_info = AddrInfo()
            addr_info.frame_start = (data & ((1 << 54) - 1)) * int(mmap.PAGESIZE)
            addr_info.offset = virtual_addr % system_page_size
            addr_info.p_addr = addr_info.frame_start + addr_info.offset
            return addr_info
        else:
            raise Exception("Could not get physical memory address for virtual address {}".format(hex(virtual_addr)))


def ctypes_alloc_aligned(size, alignment):
    # Account for a potential shift of up to (alignment-1)
    buf_size = size + alignment - 1
    # Allocate the memory as a Python byte array
    raw_memory = bytearray(buf_size + 1)

    # c_char is exactly one byte. In Python, multiplying a type T by N creates a new type that is an Array of N Ts.
    ctypes_raw_type = ctypes.c_char * buf_size
    # Instantiate my Array<c_char> that sits in raw_memory. This is only in order to get the address of raw_memory via ctypes
    ctypes_raw_memory = ctypes_raw_type.from_buffer(raw_memory)

    raw_address = ctypes.addressof(ctypes_raw_memory)
    offset = alignment - raw_address % alignment

    ctypes_aligned_type = ctypes.c_char * size
    ctypes_aligned_memory = ctypes_aligned_type.from_buffer(raw_memory, offset)

    return ctypes_aligned_memory
