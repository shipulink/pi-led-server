import time

import app.memory_utils as mu

# GPIO addresses
GPIO_BASE_PHYS = 0x20200000
GPIO_BASE_BUS = 0x7E200000

# GPIO register offsets
GPSET0 = 0x1C
GPCLR0 = 0x28


class GpioInfo:
    GPFSEL_REG_OFFSETS = [
        0x0,
        0x4,
        0x8,
        0xC,
        0x10,
        0x14
    ]

    def __init__(self, pin):
        if pin < 0 or pin > 53:
            raise Exception("Invalid gpio pin index: {}".format(pin))

        if pin <= 31:
            self.pin_flip_bit_shift = pin
            self.set_clr_register_index = 0
        else:
            self.pin_flip_bit_shift = pin - 32
            self.set_clr_register_index = 1

        gp_f_sel_ind = int(pin / 10)
        self.gp_fsel_reg_offset = self.GPFSEL_REG_OFFSETS[gp_f_sel_ind]
        self.gp_fsel_bit_offset = (pin % 10) * 3


def set_pin_fnc_to_output(gp_info):
    with mu.mmap_dev_mem(GPIO_BASE_PHYS) as m:
        mu.write_word_to_byte_array(m, gp_info.gp_fsel_reg_offset, 1 << gp_info.gp_fsel_bit_offset)

    time.sleep(0.1)
