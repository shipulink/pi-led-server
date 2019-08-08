#!/usr/bin/env python3
import app.dma as dma

PERIPHERAL_BASE_PHYS = 0x20000000
PERIPHERAL_BASE_BUS = 0x7E000000
GPIO_OFFSET = 0x200000
GPIO_BASE_PHYS = PERIPHERAL_BASE_PHYS + GPIO_OFFSET
GPIO_BASE_BUS = PERIPHERAL_BASE_BUS + GPIO_OFFSET
GPFSEL_BUS = GPIO_BASE_BUS + 0x4
GPSET0_BUS = GPIO_BASE_BUS + 0x1C
GPCLR0_BUS = GPIO_BASE_BUS + 0x28

cb_list = dma.build_linked_cb_list(2)

cb_list[0].init_source_data(4)
cb_list[0].write_word_to_source_data(0x0, 1 << 24)
cb_list[0].set_transfer_information(1 << 26)
cb_list[0].set_destination_addr(GPFSEL_BUS)

td_y = 0b11111111111111  # The Y coordinate of 2D transfer
# td_y = 10  # The Y coordinate of 2D transfer
cb_list[1].init_source_data(16 * td_y)
cb_list[1].write_word_to_source_data(0x0, 1 << 18)  # Set pin 18
cb_list[1].write_word_to_source_data(0x10 * (td_y - 1) + 0xC, 1 << 18)  # Clear pin 18
cb_list[1].set_transfer_information(1 << 26 | 0b11111 << 21 | 1 << 8 | 1 << 4 | 1 << 3 | 1 << 1)
cb_list[1].set_transfer_length_stride(16, td_y)
cb_list[1].set_stride(0, -16)
cb_list[1].set_destination_addr(GPSET0_BUS)

dma.activate_channel_with_cb(5, cb_list[0].addr)
