import ctypes
import unittest

import mmap

import app.memory_utils as mu


class TestMemoryUtils(unittest.TestCase):

    # TODO: Test more sizes and alignments (see if there's a Spock-like "where" clause)
    def test_alloc_aligned(self):
        size = 32
        alignment = 32

        m = mu.ctypes_alloc_aligned(size, alignment)
        m_addr = ctypes.addressof(m)

        self.assertEqual(len(m), size)
        self.assertEqual(m_addr % alignment, 0)

    # TODO: See if there's a way to make this function fail (like referring to
    # a variable in swap space)
    def test_virtual_to_physical(self):
        phrase = b"Helloooo world!"
        m = mu.ctypes_alloc_aligned(16, 32)
        m[0:15] = phrase
        v_addr = ctypes.addressof(m)
        addr_info = mu.virtual_to_physical_addr(v_addr)

        self.assertEqual(addr_info.p_addr, addr_info.frame_start + addr_info.offset)

        with open("/dev/mem", "r+b", buffering=0) as f:
            with mmap.mmap(f.fileno(), 4096, mmap.MAP_SHARED, mmap.PROT_READ | mmap.PROT_WRITE,
                           offset=addr_info.frame_start) as m:
                s = addr_info.offset
                self.assertEqual(m[s:s + 15], phrase)

    def test_write_word_to_byte_array(self):
        word = 0xa0b00c0d
        byte_arr = bytearray(4)
        mu.write_word_to_byte_array(byte_arr, 0, word)

        self.assertEqual(byte_arr[0], 0x0d)
        self.assertEqual(byte_arr[1], 0x0c)
        self.assertEqual(byte_arr[2], 0xb0)
        self.assertEqual(byte_arr[3], 0xa0)


if __name__ == '__main__':
    unittest.main()
