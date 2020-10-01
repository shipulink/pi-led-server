import unittest

import app.gpio as gpio


class TestMemoryUtils(unittest.TestCase):

    def setUp(self):
        return

    def test_constructor_rejects_invalid_pin_numbers(self):
        self.assertRaises(Exception, gpio.GpioInfo, -1)
        self.assertRaises(Exception, gpio.GpioInfo, 54)

    def test_constructor_calculates_correct_pin_bit_offset(self):
        self.assertEquals(0, gpio.GpioInfo(0).pin_flip_bit_shift)
        self.assertEquals(31, gpio.GpioInfo(31).pin_flip_bit_shift)
        self.assertEquals(0, gpio.GpioInfo(32).pin_flip_bit_shift)
        self.assertEquals(21, gpio.GpioInfo(53).pin_flip_bit_shift)

    def test_constructor_calculates_correct_set_and_clr_register_index(self):
        self.assertEquals(0, gpio.GpioInfo(0).set_clr_register_index)
        self.assertEquals(0, gpio.GpioInfo(31).set_clr_register_index)
        self.assertEquals(1, gpio.GpioInfo(32).set_clr_register_index)
        self.assertEquals(1, gpio.GpioInfo(53).set_clr_register_index)

    def test_constructor_calculates_correct_fsel_register_byte_offset(self):
        self.assertEquals(0, gpio.GpioInfo(0).gp_fsel_reg_offset)
        self.assertEquals(0, gpio.GpioInfo(9).gp_fsel_reg_offset)
        self.assertEquals(4, gpio.GpioInfo(10).gp_fsel_reg_offset)
        self.assertEquals(4, gpio.GpioInfo(19).gp_fsel_reg_offset)
        self.assertEquals(8, gpio.GpioInfo(20).gp_fsel_reg_offset)
        self.assertEquals(8, gpio.GpioInfo(29).gp_fsel_reg_offset)
        self.assertEquals(12, gpio.GpioInfo(30).gp_fsel_reg_offset)
        self.assertEquals(12, gpio.GpioInfo(39).gp_fsel_reg_offset)
        self.assertEquals(16, gpio.GpioInfo(40).gp_fsel_reg_offset)
        self.assertEquals(16, gpio.GpioInfo(49).gp_fsel_reg_offset)
        self.assertEquals(20, gpio.GpioInfo(50).gp_fsel_reg_offset)
        self.assertEquals(20, gpio.GpioInfo(53).gp_fsel_reg_offset)

    def test_constructor_calculates_correct_fsel_pin_bit_offset(self):
        self.assertEquals(0, gpio.GpioInfo(0).gp_fsel_bit_offset)
        self.assertEquals(15, gpio.GpioInfo(5).gp_fsel_bit_offset)
        self.assertEquals(0, gpio.GpioInfo(10).gp_fsel_bit_offset)
        self.assertEquals(21, gpio.GpioInfo(17).gp_fsel_bit_offset)


if __name__ == '__main__':
    unittest.main()
