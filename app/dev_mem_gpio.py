import time

import mmap

PERIPHERAL_BASE = 0x20000000
GPIO_OFFSET = 0x00200000
GPIO_BASE = PERIPHERAL_BASE + GPIO_OFFSET

GPFSEL1 = 0x4
GPSET0 = 0x1C
GPCLR0 = 0x28


def write_word_to_byte_array(byte_array, address, word):
    byte_array[address: address + 4] = word.to_bytes(4, byteorder='little')
    return


with open("/dev/mem", "r+b", buffering=0) as f:
    with mmap.mmap(f.fileno(), 4096, mmap.MAP_SHARED, mmap.PROT_READ | mmap.PROT_WRITE, offset=GPIO_BASE) as m:
        print(':'.join(format(x, '08b') for x in m[GPFSEL1:GPFSEL1 + 4]))
        write_word_to_byte_array(m, GPFSEL1, 0b001 << 24)
        print(':'.join(format(x, '08b') for x in m[GPFSEL1:GPFSEL1 + 4]))
        print(':'.join(format(x, '08b') for x in m[GPSET0:GPSET0 + 4]))
        write_word_to_byte_array(m, GPSET0, 0b1 << 18)
        print(':'.join(format(x, '08b') for x in m[GPSET0:GPSET0 + 4]))
        time.sleep(0.1)
        print(':'.join(format(x, '08b') for x in m[GPCLR0:GPCLR0 + 4]))
        write_word_to_byte_array(m, GPCLR0, 0b1 << 18)
        print(':'.join(format(x, '08b') for x in m[GPCLR0:GPCLR0 + 4]))
