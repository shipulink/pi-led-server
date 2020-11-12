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
        self.gp_fsel_bit_shift = (pin % 10) * 3


def set_pins_to_output(gpio_info_list):
    reg_offset_to_value_map = {}
    for gpio_info in gpio_info_list:
        reg_offset = gpio_info.gp_fsel_reg_offset
        current_value = reg_offset_to_value_map.get(reg_offset, 0)
        new_value = current_value | 1 << gpio_info.gp_fsel_bit_shift
        reg_offset_to_value_map[reg_offset] = new_value

    with mu.mmap_dev_mem(GPIO_BASE_PHYS) as m:
        for reg_offset in reg_offset_to_value_map.keys():
            value = reg_offset_to_value_map[reg_offset]
            mu.write_word_to_byte_array(m, reg_offset, value)

    time.sleep(0.1)
