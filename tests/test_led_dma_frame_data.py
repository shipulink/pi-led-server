import array
import unittest

import app.gpio as gpio
import app.led_frame_data as lfd
import app.memory_utils as mu


class LedDmaFrameData(unittest.TestCase):

    def setUp(self):
        return

    # noinspection DuplicatedCode
    def test_constructor_properly_initializes_gpio_data_array_for_holding_gpio_clr_registers_info_for_each_bit(self):
        target = lfd.LedDmaFrameData(2).gpio_data
        self.assertEqual(8 * 3 * 2, len(target))  # 8 bits per byte, 3 bytes per LED, 2 LEDs

        # The elements of gpio_data should be 2 ints for storing the bits of the two
        # gpio clr registers
        self.assertEqual(2, len(target[0]))
        self.assertTrue(isinstance(target[0][0], int))

    # noinspection DuplicatedCode
    def test_constructor_properly_initializes_address_array_for_driving_dma_cb_chain(self):
        target = lfd.LedDmaFrameData(2)
        address_array = target.bits
        expected_length = 8 * 3 * 2  # 8 bits per byte, 3 bytes per LED, 2 LEDs
        length = len(address_array)
        self.assertEqual(expected_length, length)

        # Each element should be an array of 3 ints
        self.assertEqual(3, len(address_array[0]))
        self.assertTrue(isinstance(address_array[0][0], int))

        # Each of these ints is the physical address of something:
        # The 1st int of each element is the physical address of the next element:
        second_bit_info_address = mu.get_mem_view_phys_addr_info(address_array[1]).p_addr
        self.assertEqual(second_bit_info_address, address_array[0][0])

        # An exception is the last element, whose 1st int should point to the first element's 1st int.
        first_bit_info_address = mu.get_mem_view_phys_addr_info(address_array[0]).p_addr
        self.assertEqual(first_bit_info_address, address_array[length - 1][0])

        # The third int of each element is the physical address of the first element in the clr register data array:
        first_clr_register_data_element_address = mu.get_mem_view_phys_addr_info(target.gpio_data[0]).p_addr
        self.assertEqual(first_clr_register_data_element_address, address_array[0][2])

        last_clr_register_data_element_address = mu.get_mem_view_phys_addr_info(target.gpio_data[length - 1]).p_addr
        self.assertEqual(last_clr_register_data_element_address, address_array[length - 1][2])

    def test_set_cb_addrs(self):
        target = lfd.LedDmaFrameData(2)
        address_array = target.bits
        length = len(address_array)

        data_cb_addr = 123
        stop_cb_addr = 456
        target.set_cb_addrs(data_cb_addr, stop_cb_addr)

        # set_cb_addr should set the third int of each element in the address array:
        # Every element except the last should get the first argument (address of the first CB in the loop)
        self.assertEqual(data_cb_addr, address_array[0][1])
        self.assertEqual(data_cb_addr, address_array[length - 2][1])

        # The last element should get the second argument (address of the "stop" CB of the CB loop)
        self.assertEqual(stop_cb_addr, address_array[length - 1][1])

    def test_populate_with_data_rejects_input_of_incorrect_size(self):
        target = lfd.LedDmaFrameData(2)
        byte_arr1 = array.array("B", [0b0001, 0b0010, 0b0011])
        gp_info1 = gpio.GpioInfo(12)

        self.assertRaises(Exception, target.populate_with_data, byte_arr1, gp_info1)

    def test_populate_with_data_correctly_fills_clr_register_data_array(self):
        target = lfd.LedDmaFrameData(2)
        gpio_register_data = target.gpio_data

        byte_arr1 = array.array("B", [0b0001, 0b0010, 0b0011, 0b0100, 0b0101, 0b0110])
        byte_arr2 = array.array("B", [0b0010, 0b0011, 0b0100, 0b0101, 0b0110, 0b0111])
        byte_arr3 = array.array("B", [0b0011, 0b0100, 0b0101, 0b0110, 0b0111, 0b1000])
        gp_info1 = gpio.GpioInfo(12)
        gp_info2 = gpio.GpioInfo(17)
        gp_info3 = gpio.GpioInfo(40)

        target.populate_with_data(byte_arr1, gp_info1)
        target.populate_with_data(byte_arr2, gp_info2)
        target.populate_with_data(byte_arr3, gp_info3)

        # Check data for the first gpio clr register
        self.assertEqual(1 << 12 | 1 << 17, gpio_register_data[0][0])
        self.assertEqual(1 << 12 | 1 << 17, gpio_register_data[1][0])
        self.assertEqual(1 << 12 | 1 << 17, gpio_register_data[2][0])
        self.assertEqual(1 << 12 | 1 << 17, gpio_register_data[3][0])
        self.assertEqual(1 << 12 | 1 << 17, gpio_register_data[4][0])
        self.assertEqual(1 << 12 | 1 << 17, gpio_register_data[5][0])
        self.assertEqual(1 << 12 | 0 << 17, gpio_register_data[6][0])
        self.assertEqual(0 << 12 | 1 << 17, gpio_register_data[7][0])

        self.assertEqual(1 << 12 | 1 << 17, gpio_register_data[8][0])
        self.assertEqual(1 << 12 | 1 << 17, gpio_register_data[9][0])
        self.assertEqual(1 << 12 | 1 << 17, gpio_register_data[10][0])
        self.assertEqual(1 << 12 | 1 << 17, gpio_register_data[11][0])
        self.assertEqual(1 << 12 | 1 << 17, gpio_register_data[12][0])
        self.assertEqual(1 << 12 | 1 << 17, gpio_register_data[13][0])
        self.assertEqual(0 << 12 | 0 << 17, gpio_register_data[14][0])
        self.assertEqual(1 << 12 | 0 << 17, gpio_register_data[15][0])

        self.assertEqual(1 << 12 | 1 << 17, gpio_register_data[16][0])
        self.assertEqual(1 << 12 | 1 << 17, gpio_register_data[17][0])
        self.assertEqual(1 << 12 | 1 << 17, gpio_register_data[18][0])
        self.assertEqual(1 << 12 | 1 << 17, gpio_register_data[19][0])
        self.assertEqual(1 << 12 | 1 << 17, gpio_register_data[20][0])
        self.assertEqual(1 << 12 | 0 << 17, gpio_register_data[21][0])
        self.assertEqual(0 << 12 | 1 << 17, gpio_register_data[22][0])
        self.assertEqual(0 << 12 | 1 << 17, gpio_register_data[23][0])

        self.assertEqual(1 << 12 | 1 << 17, gpio_register_data[24][0])
        self.assertEqual(1 << 12 | 1 << 17, gpio_register_data[25][0])
        self.assertEqual(1 << 12 | 1 << 17, gpio_register_data[26][0])
        self.assertEqual(1 << 12 | 1 << 17, gpio_register_data[27][0])
        self.assertEqual(1 << 12 | 1 << 17, gpio_register_data[28][0])
        self.assertEqual(0 << 12 | 0 << 17, gpio_register_data[29][0])
        self.assertEqual(1 << 12 | 1 << 17, gpio_register_data[30][0])
        self.assertEqual(1 << 12 | 0 << 17, gpio_register_data[31][0])

        self.assertEqual(1 << 12 | 1 << 17, gpio_register_data[32][0])
        self.assertEqual(1 << 12 | 1 << 17, gpio_register_data[33][0])
        self.assertEqual(1 << 12 | 1 << 17, gpio_register_data[34][0])
        self.assertEqual(1 << 12 | 1 << 17, gpio_register_data[35][0])
        self.assertEqual(1 << 12 | 1 << 17, gpio_register_data[36][0])
        self.assertEqual(0 << 12 | 0 << 17, gpio_register_data[37][0])
        self.assertEqual(1 << 12 | 0 << 17, gpio_register_data[38][0])
        self.assertEqual(0 << 12 | 1 << 17, gpio_register_data[39][0])

        self.assertEqual(1 << 12 | 1 << 17, gpio_register_data[40][0])
        self.assertEqual(1 << 12 | 1 << 17, gpio_register_data[41][0])
        self.assertEqual(1 << 12 | 1 << 17, gpio_register_data[42][0])
        self.assertEqual(1 << 12 | 1 << 17, gpio_register_data[43][0])
        self.assertEqual(1 << 12 | 1 << 17, gpio_register_data[44][0])
        self.assertEqual(0 << 12 | 0 << 17, gpio_register_data[45][0])
        self.assertEqual(0 << 12 | 0 << 17, gpio_register_data[46][0])
        self.assertEqual(1 << 12 | 0 << 17, gpio_register_data[47][0])

        # Check data for the second gpio clr register
        self.assertEqual(1 << 8, gpio_register_data[0][1])
        self.assertEqual(1 << 8, gpio_register_data[1][1])
        self.assertEqual(1 << 8, gpio_register_data[2][1])
        self.assertEqual(1 << 8, gpio_register_data[3][1])
        self.assertEqual(1 << 8, gpio_register_data[4][1])
        self.assertEqual(1 << 8, gpio_register_data[5][1])
        self.assertEqual(0 << 8, gpio_register_data[6][1])
        self.assertEqual(0 << 8, gpio_register_data[7][1])

        self.assertEqual(1 << 8, gpio_register_data[8][1])
        self.assertEqual(1 << 8, gpio_register_data[9][1])
        self.assertEqual(1 << 8, gpio_register_data[10][1])
        self.assertEqual(1 << 8, gpio_register_data[11][1])
        self.assertEqual(1 << 8, gpio_register_data[12][1])
        self.assertEqual(0 << 8, gpio_register_data[13][1])
        self.assertEqual(1 << 8, gpio_register_data[14][1])
        self.assertEqual(1 << 8, gpio_register_data[15][1])

        self.assertEqual(1 << 8, gpio_register_data[16][1])
        self.assertEqual(1 << 8, gpio_register_data[17][1])
        self.assertEqual(1 << 8, gpio_register_data[18][1])
        self.assertEqual(1 << 8, gpio_register_data[19][1])
        self.assertEqual(1 << 8, gpio_register_data[20][1])
        self.assertEqual(0 << 8, gpio_register_data[21][1])
        self.assertEqual(1 << 8, gpio_register_data[22][1])
        self.assertEqual(0 << 8, gpio_register_data[23][1])

        self.assertEqual(1 << 8, gpio_register_data[24][1])
        self.assertEqual(1 << 8, gpio_register_data[25][1])
        self.assertEqual(1 << 8, gpio_register_data[26][1])
        self.assertEqual(1 << 8, gpio_register_data[27][1])
        self.assertEqual(1 << 8, gpio_register_data[28][1])
        self.assertEqual(0 << 8, gpio_register_data[29][1])
        self.assertEqual(0 << 8, gpio_register_data[30][1])
        self.assertEqual(1 << 8, gpio_register_data[31][1])

        self.assertEqual(1 << 8, gpio_register_data[32][1])
        self.assertEqual(1 << 8, gpio_register_data[33][1])
        self.assertEqual(1 << 8, gpio_register_data[34][1])
        self.assertEqual(1 << 8, gpio_register_data[35][1])
        self.assertEqual(1 << 8, gpio_register_data[36][1])
        self.assertEqual(0 << 8, gpio_register_data[37][1])
        self.assertEqual(0 << 8, gpio_register_data[38][1])
        self.assertEqual(0 << 8, gpio_register_data[39][1])

        self.assertEqual(1 << 8, gpio_register_data[40][1])
        self.assertEqual(1 << 8, gpio_register_data[41][1])
        self.assertEqual(1 << 8, gpio_register_data[42][1])
        self.assertEqual(1 << 8, gpio_register_data[43][1])
        self.assertEqual(0 << 8, gpio_register_data[44][1])
        self.assertEqual(1 << 8, gpio_register_data[45][1])
        self.assertEqual(1 << 8, gpio_register_data[46][1])
        self.assertEqual(1 << 8, gpio_register_data[47][1])


if __name__ == '__main__':
    unittest.main()
