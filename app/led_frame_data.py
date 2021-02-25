import os

import app.memory_utils as mu


def flatten_array_of_byte_arrays(data):
    i = 0
    flat_data = bytearray(len(data) * 3)
    while i < len(data):
        flat_data[i * 3] = data[i][1]
        flat_data[i * 3 + 1] = data[i][0]
        flat_data[i * 3 + 2] = data[i][2]
        i += 1
    return flat_data


def get_register_value_for_bit(byte_array: bytearray, bit_shifts: [int], bit_index):
    reg_val = 0
    i = 0
    num_bytes = len(byte_array)
    while i < num_bytes:
        byte = byte_array[i]
        bit_shift = bit_shifts[i]
        if byte & (128 >> bit_index) == 0:
            reg_val |= 1 << bit_shift
        i += 1
    return reg_val


class LedDmaFrameData:
    def __init__(self, num_leds):
        self.data_cb_addr = None
        self.stop_cb_addr = None
        self.num_leds = num_leds
        self.num_words_per_bit = 3
        self.num_bits = self.num_leds * 3 * 8  # 3 bytes per LED (RGB), 8 bits per byte

        # Create an array of 2-word memory views to hold GPIO CLR register data for each bit, and both CLR registers.
        self.gpio_data = mu.create_phys_contig_int_views(2, self.num_bits)

        # For every bit, create an int array of size 3. Each int will hold a physical memory address
        self.bits = mu.create_phys_contig_int_views(self.num_words_per_bit, self.num_bits)
        self.start_address = mu.get_mem_view_phys_addr_info(self.bits[0]).p_addr

        # Fill the first slot of every 3-int array with the address of the next 3-int array.
        # Fill the last slot of every 3-int array with the address of the bit's gpio_data slot's address
        with open("/proc/" + str(os.getpid()) + "/pagemap", "r+b") as pagemap_fd:
            i = 0
            while i < self.num_bits:
                if i < self.num_bits - 1:
                    self.bits[i][0] = mu.get_mem_view_phys_addr_info_with_pagemap(self.bits[i + 1], pagemap_fd).p_addr
                self.bits[i][2] = mu.get_mem_view_phys_addr_info_with_pagemap(self.gpio_data[i], pagemap_fd).p_addr
                i += 1

        # Set the first slot of the last 3-int array to the address of the first one,
        # resetting the DMA CB loop to the first bit of the next frame
        self.bits[self.num_bits - 1][0] = mu.get_mem_view_phys_addr_info(self.bits[0]).p_addr

    def set_cb_addrs(self, data_cb_addr, stop_cb_addr):
        self.data_cb_addr = data_cb_addr
        self.stop_cb_addr = stop_cb_addr

        # For the purpose of stopping the CB loop at the right time,
        # fill the third slot of every 3-int array with the address of the first CB in the CB loop,
        # except for the last bit. The last bit should point to the address of the CB that will be used
        # to get out of the data loop and into the idle loop.
        i = 0
        while i < self.num_bits - 1:
            self.bits[i][1] = data_cb_addr
            i += 1
        self.bits[self.num_bits - 1][1] = self.stop_cb_addr

    def populate_with_data_single_register(self, data, bit_shifts, register_index):
        num_pins = len(data)
        num_leds = len(data[0])

        led_ind = 0
        while led_ind < num_leds:
            # lists of r, g, and b bytes for each pin for the current LED index:
            r_list = bytearray(num_pins)
            g_list = bytearray(num_pins)
            b_list = bytearray(num_pins)
            pin_ind = 0
            while pin_ind < num_pins:
                rgb = data[pin_ind][led_ind]
                r_list[pin_ind] = rgb[0]
                g_list[pin_ind] = rgb[1]
                b_list[pin_ind] = rgb[2]
                pin_ind += 1

            bit_sub_ind = 0  # index of bit within the current byte
            bit_ind_g = led_ind * 3 * 8
            bit_ind_r = bit_ind_g + 8
            bit_ind_b = bit_ind_r + 8
            while bit_sub_ind < 8:
                reg_val_g = get_register_value_for_bit(g_list, bit_shifts, bit_sub_ind)
                reg_val_r = get_register_value_for_bit(r_list, bit_shifts, bit_sub_ind)
                reg_val_b = get_register_value_for_bit(b_list, bit_shifts, bit_sub_ind)

                self.gpio_data[bit_ind_g][register_index] = reg_val_g
                self.gpio_data[bit_ind_r][register_index] = reg_val_r
                self.gpio_data[bit_ind_b][register_index] = reg_val_b

                bit_ind_g += 1
                bit_ind_r += 1
                bit_ind_b += 1
                bit_sub_ind += 1
            led_ind += 1

    # data is an array, where each element is a blob of RGB data for a single strip / gpio pin.
    # Each blob is itself an array of bytearrays.
    # Each bytearray has length 3 and represents the RGB data for a single LED.
    def populate_with_data(self, data, gpio_info_list):
        if len(data) != len(gpio_info_list):
            raise Exception("Length of frame data must match the number of gpio pins in use.")

        # Separate data lists into two buckets - one for each GPIO CLR register:
        data_grouped_by_reg = [[]] * 2
        bit_shifts_grouped_by_reg = [[]] * 2

        num_pins = len(gpio_info_list)
        i = 0
        while i < num_pins:
            gpio_info = gpio_info_list[i]
            reg_ind = gpio_info.set_clr_register_index
            data_grouped_by_reg[reg_ind].append(data[i])
            bit_shifts_grouped_by_reg[reg_ind].append(gpio_info.pin_flip_bit_shift)
            i += 1

        self.populate_with_data_single_register(data_grouped_by_reg[0], bit_shifts_grouped_by_reg[0], 0)
        self.populate_with_data_single_register(data_grouped_by_reg[1], bit_shifts_grouped_by_reg[1], 1)
