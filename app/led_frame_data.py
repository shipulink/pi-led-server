import app.memory_utils as mu


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
        i = 0
        while i < self.num_bits:
            if i < self.num_bits - 1:
                self.bits[i][0] = mu.get_mem_view_phys_addr_info(self.bits[i + 1]).p_addr
            self.bits[i][2] = mu.get_mem_view_phys_addr_info(self.gpio_data[i]).p_addr
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

    def populate_with_data(self, data, gpio_info):
        num_bytes = self.num_leds * 3
        if len(data) != num_bytes:
            raise Exception("This LedFrameData instance was initialized for exactly {} bytes of data. "
                            "The supplied data must be {} bytes long.".format(num_bytes, num_bytes))

        i = 0
        while i < num_bytes:
            byte = data[i]
            j = 0
            while j < 8:
                bit_ind = 8 * i + j
                if byte & (128 >> j) == 0:
                    self.gpio_data[bit_ind][gpio_info.set_clr_register_index] |= 1 << gpio_info.pin_flip_bit_shift
                j += 1
            i += 1
