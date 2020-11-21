import unittest

import app.pwm as pwm


class TestMemoryUtils(unittest.TestCase):

    def setUp(self):
        return

    def test_configure_and_start_pwm_raises_exception_for_invalid_clock_source(self):
        invalid_clock_source_index = 2
        self.assertRaises(Exception, pwm.configure_and_start_pwm, 2, invalid_clock_source_index, 2, 0, 16)

    def test_configure_and_start_pwm_raises_exception_for_invalid_divider_integer_part(self):
        invalid_integer_divider = 1
        self.assertRaises(Exception, pwm.configure_and_start_pwm, 2, 1, invalid_integer_divider, 0, 16)

    def test_configure_and_start_pwm_raises_exception_for_invalid_divider_fraction_part(self):
        invalid_fraction_divider_too_low = -1
        invalid_fraction_divider_too_high = 4096
        self.assertRaises(Exception, pwm.configure_and_start_pwm, 2, 1, 2, invalid_fraction_divider_too_low, 16)
        self.assertRaises(Exception, pwm.configure_and_start_pwm, 2, 1, 2, invalid_fraction_divider_too_high, 16)

    def test_stop_pwm_raises_exception_for_invalid_clock_source(self):
        invalid_clock_source_index = 2
        self.assertRaises(Exception, pwm.stop_pwm, 2, invalid_clock_source_index)


if __name__ == '__main__':
    unittest.main()
