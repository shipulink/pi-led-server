import unittest

import app.dma as dma
import app.memory_utils as mu


class TestMemoryUtils(unittest.TestCase):

    def setUp(self):
        self.mv = mu.create_phys_contig_int_view(32)

    def test_constructor_requires_zero_or_two_arguments(self):
        self.assertRaises(Exception, dma.ControlBlock, shared_mem_view=self.mv)
        self.assertRaises(Exception, dma.ControlBlock, word_offset=8)

    def test_constructor_requires_word_offset_multiple_of_8(self):
        self.assertRaises(Exception, dma.ControlBlock, self.mv, 12)

    def test_constructor_defaults(self):
        target = dma.ControlBlock()
        self.assertEqual(0, target.word_offset)
        self.assertEqual(16, len(target.shared_mem))


if __name__ == '__main__':
    unittest.main()
