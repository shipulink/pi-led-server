import unittest

import random

import app.dma as dma
import app.memory_utils as mu


class TestMemoryUtils(unittest.TestCase):

    def setUp(self):
        self.OFFSET_WORDS_TI = 0
        self.OFFSET_WORDS_SRC_ADDR = 1
        self.OFFSET_WORDS_DEST_ADDR = 2
        self.OFFSET_WORDS_TXFR_LEN = 3
        self.OFFSET_WORDS_STRIDE = 4
        self.OFFSET_WORDS_NEXT_CB_ADDR = 5
        self.OFFSET_WORDS_DATA_DEFAULT = 8
        self.mv = mu.create_aligned_phys_contig_int_view(32, 32)

    def test_constructor_requires_zero_or_two_arguments(self):
        self.assertRaises(Exception, dma.ControlBlock, shared_mem_view=self.mv)
        self.assertRaises(Exception, dma.ControlBlock, word_offset=8)

    def test_constructor_requires_word_offset_to_be_multiple_of_8(self):
        self.assertRaises(Exception, dma.ControlBlock, self.mv, 12)

    def test_constructor_requires_shared_mem_view_to_be_32_byte_aligned(self):
        self.assertRaises(Exception, dma.ControlBlock, self.mv[1:], 0)

    def test_constructor_defaults(self):
        target = dma.ControlBlock()
        self.assertEqual(0, target.word_offset)
        self.assertEqual(16, len(target.shared_mem))

    def test_constructor_calculate_correct_cb_address(self):
        cb_word_offset = 16
        target = dma.ControlBlock(self.mv, cb_word_offset)
        expected_address = mu.get_mem_view_phys_addr_info(self.mv).p_addr + 4 * cb_word_offset
        self.assertEqual(expected_address, target.addr)

    def test_constructor_sets_transfer_length_to_one_word_by_default(self):
        cb_word_offset = 16
        dma.ControlBlock(self.mv, cb_word_offset)
        expected_transfer_length = 4
        self.assertEqual(expected_transfer_length, self.mv[cb_word_offset + self.OFFSET_WORDS_TXFR_LEN])

    def test_constructor_sets_src_addr_to_an_address_in_shared_memory_of_cb(self):
        cb_word_offset = 16
        dma.ControlBlock(self.mv, cb_word_offset)
        expected_src_addr = mu.get_mem_view_phys_addr_info(self.mv[cb_word_offset + self.OFFSET_WORDS_DATA_DEFAULT:]).p_addr
        self.assertEqual(expected_src_addr, self.mv[cb_word_offset + self.OFFSET_WORDS_SRC_ADDR])

    def test_set_transfer_information(self):
        cb_word_offset = 16
        target = dma.ControlBlock(self.mv, cb_word_offset)
        transfer_information = random.randint(0, 0xFFFFFFFF)
        target.set_transfer_information(transfer_information)
        self.assertEqual(transfer_information, self.mv[cb_word_offset + self.OFFSET_WORDS_TI])

    def test_set_source_addr(self):
        cb_word_offset = 16
        target = dma.ControlBlock(self.mv, cb_word_offset)
        source_addr = random.randint(0, 0xFFFFFFFF)
        target.set_source_addr(source_addr)
        self.assertEqual(source_addr, self.mv[cb_word_offset + self.OFFSET_WORDS_SRC_ADDR])

    def test_set_destination_addr(self):
        cb_word_offset = 16
        target = dma.ControlBlock(self.mv, cb_word_offset)
        destination_addr = random.randint(0, 0xFFFFFFFF)
        target.set_destination_addr(destination_addr)
        self.assertEqual(destination_addr, self.mv[cb_word_offset + self.OFFSET_WORDS_DEST_ADDR])

    def test_set_transfer_length(self):
        cb_word_offset = 16
        target = dma.ControlBlock(self.mv, cb_word_offset)
        transfer_length = random.randint(0, 0xFFFFFFFF)
        target.set_transfer_length(transfer_length)
        self.assertEqual(transfer_length, self.mv[cb_word_offset + self.OFFSET_WORDS_TXFR_LEN])

    def test_set_transfer_length_stride(self):
        cb_word_offset = 16
        target = dma.ControlBlock(self.mv, cb_word_offset)
        transfer_length_x = random.randint(0, 0xFFFF)
        transfer_length_y = random.randint(0, 0xFFFF)
        transfer_length = transfer_length_x | (transfer_length_y - 1) << 16
        target.set_transfer_length_stride(transfer_length_x, transfer_length_y)
        self.assertEqual(transfer_length, self.mv[cb_word_offset + self.OFFSET_WORDS_TXFR_LEN])

    def test_set_stride(self):
        cb_word_offset = 16
        target = dma.ControlBlock(self.mv, cb_word_offset)
        stride_src = random.randint(0, 0xFFFF)
        stride_dest = random.randint(0, 0xFFFF)
        stride = stride_src | stride_dest << 16
        target.set_stride(stride_src, stride_dest)
        self.assertEqual(stride, self.mv[cb_word_offset + self.OFFSET_WORDS_STRIDE])

    def test_set_next_cb_addr(self):
        cb_word_offset = 16
        target = dma.ControlBlock(self.mv, cb_word_offset)
        next_cb_addr = random.randint(0, 0xFFFFFFFF)
        target.set_next_cb_addr(next_cb_addr)
        self.assertEqual(next_cb_addr, self.mv[cb_word_offset + self.OFFSET_WORDS_NEXT_CB_ADDR])

    def test_write_word_to_source_data(self):
        cb_word_offset = 16
        target = dma.ControlBlock(self.mv, cb_word_offset)
        word = random.randint(0, 0xFFFFFFFF)
        write_offset = 3
        target.write_word_to_source_data(write_offset, word)
        self.assertEqual(word, self.mv[cb_word_offset + write_offset + self.OFFSET_WORDS_DATA_DEFAULT])


if __name__ == '__main__':
    unittest.main()
