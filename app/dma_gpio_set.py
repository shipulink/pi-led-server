#!/usr/bin/env python3
import mmap

import app.dma as dma

PERIPHERAL_BASE_PHYS = 0x20000000
PERIPHERAL_BASE_BUS = 0x7E000000
GPIO_OFFSET = 0x200000
GPIO_BASE_PHYS = PERIPHERAL_BASE_PHYS + GPIO_OFFSET
GPIO_BASE_BUS = PERIPHERAL_BASE_BUS + GPIO_OFFSET

data_len = 4  # bytes

cb = dma.ControlBlock()
cb.init_source_data(data_len)
cb.write_word_to_source_data(0x0, 1<<24)
cb.set_transfer_information(1 << 26)
cb.set_destination_addr(GPIO_BASE_BUS + 0x4)

with open("/dev/mem", "r+b", buffering=0) as f:
    with mmap.mmap(f.fileno(), 4096, mmap.MAP_SHARED, mmap.PROT_READ | mmap.PROT_WRITE,
                   offset=GPIO_BASE_PHYS) as gpio_mem:
        print(':'.join(format(x, 'x') for x in gpio_mem[0x4:0x4 + data_len]))

dma.activate_channel_with_cb(0, cb.addr)

with open("/dev/mem", "r+b", buffering=0) as f:
    with mmap.mmap(f.fileno(), 4096, mmap.MAP_SHARED, mmap.PROT_READ | mmap.PROT_WRITE,
                   offset=GPIO_BASE_PHYS) as gpio_mem:
        print(':'.join(format(x, 'x') for x in gpio_mem[0x4:0x4 + data_len]))
