import unittest

import struct

import app.dma as dma
import app.memory_utils as mu


class TestMemoryUtils(unittest.TestCase):

    def setUp(self):
        self.cb = dma.ControlBlock()

    def test_activate_channel_with_cb_rejects_invalid_channels(self):
        self.assertRaises(Exception, dma.activate_channel_with_cb, -1, self.cb.addr)
        self.assertRaises(Exception, dma.activate_channel_with_cb, 16, self.cb.addr)

    # noinspection DuplicatedCode
    def test_activate_channel_with_cb_resets_cs_register_and_sets_defaults(self):
        channel = 2
        dma.activate_channel_with_cb(channel, self.cb.addr, False)
        with mu.mmap_dev_mem(dma.DMA_BASE_PHYS) as m:
            channel_offset = 0x100 * channel
            cs_register_offset = channel_offset + dma.DMA_CS
            cs_register = struct.unpack('<L', m[cs_register_offset:cs_register_offset + 4])[0]
            self.assertFalse(is_nth_bit_set(cs_register, 0))  # Not active
            self.assertFalse(is_nth_bit_set(cs_register, 1))  # No control block has been completed
            self.assertFalse(is_nth_bit_set(cs_register, 2))  # Channel has not produced an interrupt
            self.assertFalse(is_nth_bit_set(cs_register, 4))  # Not paused, because it hasn't started yet
            self.assertFalse(is_nth_bit_set(cs_register, 5))  # Not paused by DREQ
            self.assertFalse(is_nth_bit_set(cs_register, 6))  # Not waiting for any writes to complete
            self.assertFalse(is_nth_bit_set(cs_register, 8))  # No errors detected

            # AXI Priority is 8
            self.assertFalse(is_nth_bit_set(cs_register, 16))
            self.assertFalse(is_nth_bit_set(cs_register, 17))
            self.assertFalse(is_nth_bit_set(cs_register, 18))
            self.assertTrue(is_nth_bit_set(cs_register, 19))

            # AXI Panic Priority is 8
            self.assertFalse(is_nth_bit_set(cs_register, 20))
            self.assertFalse(is_nth_bit_set(cs_register, 21))
            self.assertFalse(is_nth_bit_set(cs_register, 22))
            self.assertTrue(is_nth_bit_set(cs_register, 23))

            self.assertTrue(is_nth_bit_set(cs_register, 28))  # Channel configured to wait for outstanding writes
            self.assertFalse(is_nth_bit_set(cs_register, 29))  # Debug pause signal is honored

    # noinspection DuplicatedCode
    def test_activate_channel_with_cb_resets_debug_register_and_clears_errors(self):
        channel = 2
        dma.activate_channel_with_cb(channel, self.cb.addr, False)
        with mu.mmap_dev_mem(dma.DMA_BASE_PHYS) as m:
            channel_offset = 0x100 * channel
            debug_register_offset = channel_offset + dma.DMA_DEBUG
            debug_register = struct.unpack('<L', m[debug_register_offset:debug_register_offset + 4])[0]
            self.assertFalse(is_nth_bit_set(debug_register, 0))  # No read last not set error
            self.assertFalse(is_nth_bit_set(debug_register, 1))  # No FIFO error
            self.assertFalse(is_nth_bit_set(debug_register, 2))  # No slave response error

            # Zero outstanding writes
            self.assertFalse(is_nth_bit_set(debug_register, 4))
            self.assertFalse(is_nth_bit_set(debug_register, 5))
            self.assertFalse(is_nth_bit_set(debug_register, 6))
            self.assertFalse(is_nth_bit_set(debug_register, 7))

    # noinspection DuplicatedCode
    def test_activate_channel_with_cb_writes_cb_address_to_cb_address_register(self):
        channel = 2
        dma.activate_channel_with_cb(channel, self.cb.addr, False)
        with mu.mmap_dev_mem(dma.DMA_BASE_PHYS) as m:
            channel_offset = 0x100 * channel
            cb_addr_register_offset = channel_offset + dma.DMA_CB_AD
            cb_addr_register = struct.unpack('<L', m[cb_addr_register_offset:cb_addr_register_offset + 4])[0]
            self.assertEquals(self.cb.addr, cb_addr_register)


def is_nth_bit_set(word, n):
    return word & (1 << n)


if __name__ == '__main__':
    unittest.main()
