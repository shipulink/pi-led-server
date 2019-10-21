import math

import app.memory_utils as mu


class LedDmaFrameData:
    def __init__(self, num_leds):
        self.zero_cb_addr = None
        self.one_cb_addr = None
        self.stop_cb_addr = None
        self.byte_reps = [bytes() for i in range(256)]
        self.num_leds = num_leds
        self.view_len = 256
        num_bits = self.num_leds * 3 * 8 + 1  # 3 bytes per LED (RGB), 8 bits per byte, plus 1 for the "stop" CB address
        self.total_len = num_bits * 2  # half the indices will contain CB-lilinking addrs, half will contain GPIO dest addrs
        self.num_views = math.ceil(self.total_len / self.view_len)
        self.mvs = mu.create_phys_contig_int_views(256, self.num_views)

        # Calculate the physical memory addresses of the first index of each mv:
        i = 0
        self.base_addrs = []
        while i < self.num_views:
            self.base_addrs.append(mu.get_mem_view_phys_addr_info(self.mvs[i]).p_addr)
            i += 1

        # Fill in the CB-linking next_cb_addr info:
        i = 0
        while i < self.num_views:
            if i == self.num_views - 1:
                last_ind = int((self.total_len % self.view_len) / 2 - 1)
                next_base_addr = self.base_addrs[0]  # link to the first index of first CB
            else:
                last_ind = int(self.view_len / 2 - 1)
                next_base_addr = self.base_addrs[i + 1]  # link to the first index of the next CB
            base_addr = self.base_addrs[i]

            j = 0
            while j < last_ind:
                self.mvs[i][j] = base_addr + 4 * (j + 1)
                j += 1
            self.mvs[i][last_ind] = next_base_addr
            i += 1

    def set_cb_addrs(self, zero_cb_addr, one_cb_addr, stop_cb_addr):
        self.zero_cb_addr = zero_cb_addr
        self.one_cb_addr = one_cb_addr
        self.stop_cb_addr = stop_cb_addr
        i = 0
        while i < 256:
            self.byte_reps[i] = generate_target_addrs_for_byte(i, self.zero_cb_addr, self.one_cb_addr)
            i += 1
        self.mvs[self.num_views - 1][int((self.view_len + self.total_len % self.view_len) / 2 - 1)] = self.stop_cb_addr

    def populate_with_data(self, data):
        # TODO: make sure data has the right number of bytes
        i = 0
        byte_ind = 0
        while i < self.num_views:
            if i == self.num_views - 1:
                last_ind = int((self.view_len + self.total_len % self.view_len) / 2 - 9)
            else:
                last_ind = self.view_len - 8
            j = int(self.view_len / 2)
            while j <= last_ind:
                self.mvs[i][j: j + 8] = self.byte_reps[data[byte_ind]]
                byte_ind += 1
                j += 8
            i += 1

    def print_debug_info(self):
        i = 0
        while i < self.num_views:
            print(format(self.base_addrs[i], '08x'))
            print(':'.join(format(x, '08x') for x in self.mvs[i]))
            i += 1


def generate_target_addrs_for_byte(byte, ad_zero, ad_one):
    byte_rep = mu.create_int_mem_view(8)
    i = 0
    while i < 8:
        if byte & (128 >> i) == 0:
            byte_rep[i] = ad_zero
        else:
            byte_rep[i] = ad_one
        i += 1
    return byte_rep
