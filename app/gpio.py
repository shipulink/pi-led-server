import time

import app.memory_utils as mu

GPIO_BASE = 0x20200000
GPIO_BASE_BUS = 0x7E200000

GPSET0_REG_OFFSET = 0x1C
GPSET1_REG_OFFSET = 0x20

GPCLR0_REG_OFFSET = 0x28
GPCLR1_REG_OFFSET = 0x2C

GPFSEL_REG_OFFSETS = [
    0x0,
    0x4,
    0x8,
    0xC,
    0x10,
    0x14
]


class GpioInfo:
    def __init__(self, pin):
        if pin < 0 or pin > 53:
            raise Exception("Invalid gpio pin index: {}".format(pin))

        if pin <= 31:
            self.set_reg_offset = GPSET0_REG_OFFSET
            self.clr_reg_offset = GPCLR0_REG_OFFSET
            self.pin_flip_bit_shift = pin
            self.set_clr_register_index = 0
        else:
            self.set_reg_offset = GPSET1_REG_OFFSET
            self.clr_reg_offset = GPCLR1_REG_OFFSET
            self.pin_flip_bit_shift = pin - 32
            self.set_clr_register_index = 0

        gp_f_sel_ind = int(pin / 10)
        self.gp_fsel_reg_offset = GPFSEL_REG_OFFSETS[gp_f_sel_ind]
        self.gp_fsel_bit_offset = (pin % 10) * 3


def set_pin_fnc_to_output(gp_info):
    with mu.mmap_dev_mem(GPIO_BASE) as m:
        mu.write_word_to_byte_array(m, gp_info.gp_fsel_reg_offset, 1 << gp_info.gp_fsel_bit_offset)

    time.sleep(0.1)
