import unittest

import struct

import app.gpio as gpio
import app.memory_utils as mu


class TestMemoryUtils(unittest.TestCase):

    def setUp(self):
        return

    def test_set_pins_to_output_sets_correct_bits_of_correct_registers(self):
        with mu.mmap_dev_mem(gpio.GPIO_BASE_PHYS) as m:

            # Set all pins in GPFSEL1 register to input (000) and check that the write was successful
            gpfsel1_reg_offset = 0x4
            mu.write_word_to_byte_array(m, gpfsel1_reg_offset, 0)
            gpfsel1_reg_value = struct.unpack('<L', m[gpfsel1_reg_offset:gpfsel1_reg_offset + 4])[0]
            self.assertEqual(0, gpfsel1_reg_value)

            # Set pins 15 and 18 to output and check that the register bits are set as expected
            gpio_info15 = gpio.GpioInfo(15)
            gpio_info18 = gpio.GpioInfo(18)
            gpio.set_pins_to_output([gpio_info15, gpio_info18])
            expected_gpfsel1_reg_value = 1 << 15 | 1 << 24
            gpfsel1_reg_value = struct.unpack('<L', m[gpfsel1_reg_offset:gpfsel1_reg_offset + 4])[0]
            self.assertEqual(expected_gpfsel1_reg_value, gpfsel1_reg_value)


if __name__ == '__main__':
    unittest.main()
