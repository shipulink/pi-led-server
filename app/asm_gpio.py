import array
import ctypes

import mmap
import os

# Open /dev/gpiomem as file and get a pointer to its
# address in the program's virtual address space
file = os.open("/dev/gpiomem", os.O_RDWR | os.O_SYNC)
mapping = mmap.mmap(file, 4096, mmap.MAP_SHARED, mmap.PROT_READ | mmap.PROT_WRITE)
mapping_as_int = ctypes.c_int.from_buffer(mapping)
addr = ctypes.addressof(mapping_as_int)

# Load the LED library
current_dir = os.path.dirname(__file__)
lib_abs_path = os.path.abspath(os.path.join(current_dir, "lib.so"))
lib = ctypes.CDLL(lib_abs_path)

# Test GPIO
#lib.init_gpio(addr)

#while True:
#    lib.send_zero(addr)
#    lib.send_one(addr)

# Test assesmbly int array reading:
# This is an int representation of the string "Hi, Vivian!"
#ints = [72, 105, 44, 32, 86, 105, 118, 105, 97, 110, 33, 00]
#byte_arr = array.array("B", ints)
# TODO: change from .tostring() to .tobytes() if moving to Python 3.2 or later.
#bytes = byte_arr.tostring()
#byte_addr = ctypes.c_char_p(bytes)
#lib.read_buffer(byte_addr)

# Test sending a byte:
#lib.init_gpio(addr)

#while True:
#    lib.send_byte(addr, 240)
#lib.send_byte(addr, 240)


# Test sending byte array
ints = [240, 240, 240]
byte_arr = array.array("B", ints)
bytes = byte_arr.tostring()
byte_addr = ctypes.c_char_p(bytes)

lib.init_gpio(addr)

while True:
    lib.send_byte_array(addr, byte_addr, len(ints))