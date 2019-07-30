import ctypes
import os
import mmap


class AddrInfo:
    def __init__(self):
        self.frame_start = None
        self.offset = None


def virtual_to_physical_addr(virtual_addr):
    # Data in pagemap is stored in 64-bit (8-byte) chunks. One per mapping.
    mapping_info_length = 8

    system_page_size = mmap.PAGESIZE
    pagemap_fd = open("/proc/" + str(os.getpid()) + "/pagemap", "r+b")

    pagemap_fd.seek(int(virtual_addr / system_page_size) * mapping_info_length)
    data_bytes = pagemap_fd.read(mapping_info_length)
    data = int.from_bytes(data_bytes, 'little')

    if ((data >> 63) & 1) == 1:
        addr_info = AddrInfo()
        addr_info.frame_start = (data & ((1 << 54) - 1)) * int(mmap.PAGESIZE)
        addr_info.offset = virtual_addr % system_page_size
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


# thing = ctypes_alloc_aligned(16, 32)
# thing[0:15] = b"Helloooo world!"
# v_addr = ctypes.addressof(thing)
# p_addr = virtual_to_physical_addr(v_addr)
# print(p_addr.frame_start)
# print(p_addr.offset)
#
# with open("/dev/mem", "r+b", buffering=0) as f:
#     with mmap.mmap(f.fileno(), 4096, mmap.MAP_SHARED, mmap.PROT_READ | mmap.PROT_WRITE, offset=p_addr.frame_start) as m:
#         s = p_addr.offset
#         print(m[s:s + 15].decode("utf-8"))
