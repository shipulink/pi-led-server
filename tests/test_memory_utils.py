import array
import ctypes
import mmap
import unittest

import app.memory_utils as mu


class TestMemoryUtils(unittest.TestCase):

    def test_virtual_to_physical_addr(self):
        initial_value = 0
        dummy_item = ctypes.c_int(initial_value)
        virtual_address = ctypes.addressof(dummy_item)
        p_addr_info = mu.virtual_to_physical_addr(virtual_address)
        self.assertEqual(p_addr_info.frame_start + p_addr_info.offset, p_addr_info.p_addr)
        self.assertEqual(initial_value, dummy_item.value)

        new_value = 123
        with mu.mmap_dev_mem(p_addr_info.frame_start) as m:
            m[p_addr_info.offset] = new_value
        self.assertEqual(new_value, dummy_item.value)

    def test_get_mem_view_phys_addr_info(self):
        view_len = 10
        mv = memoryview(array.array('L', [0] * view_len))
        c_type_mv = ctypes.c_char.from_buffer(mv)
        v_addr = ctypes.addressof(c_type_mv)
        p_addr_info_expected = mu.virtual_to_physical_addr(v_addr)

        p_addr_info = mu.get_mem_view_phys_addr_info(mv)

        self.assertEqual(p_addr_info_expected.frame_start, p_addr_info.frame_start)
        self.assertEqual(p_addr_info_expected.offset, p_addr_info.offset)
        self.assertEqual(p_addr_info_expected.p_addr, p_addr_info.p_addr)

    def test_write_word_to_byte_array(self):
        word = 0xa0b00c0d
        byte_arr = bytearray(4)
        mu.write_word_to_byte_array(byte_arr, 0, word)

        self.assertEqual(byte_arr[0], 0x0d)
        self.assertEqual(byte_arr[1], 0x0c)
        self.assertEqual(byte_arr[2], 0xb0)
        self.assertEqual(byte_arr[3], 0xa0)

    def test_check_int_mem_view_physical_contiguous(self):
        # Make a memoryview of a single byte, so that it must be contiguous
        mv_contiguous = memoryview(array.array('L', [0] * 1))
        self.assertTrue(mu.check_int_mem_view_physical_contiguous(mv_contiguous))

        # Make a memoryview larger than system page size, so that it cannot be contiguous
        mv_non_contiguous = memoryview(array.array('L', [0] * mmap.PAGESIZE * 2))
        self.assertFalse(mu.check_int_mem_view_physical_contiguous(mv_non_contiguous))


if __name__ == '__main__':
    unittest.main()
