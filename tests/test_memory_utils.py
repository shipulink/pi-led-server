import unittest
import ctypes
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

if __name__ == '__main__':
    unittest.main()