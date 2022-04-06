import time
import unittest


# import app.dma as dma


def transpose32(gpio_data):
    ##formatter:off
    t = (gpio_data[0] ^ (gpio_data[16] >> 16)) & 0x0000FFFF; gpio_data[0] ^= t; gpio_data[16] ^= (t << 16)
    t = (gpio_data[1] ^ (gpio_data[17] >> 16)) & 0x0000FFFF; gpio_data[1] ^= t; gpio_data[17] ^= (t << 16)
    t = (gpio_data[2] ^ (gpio_data[18] >> 16)) & 0x0000FFFF; gpio_data[2] ^= t; gpio_data[18] ^= (t << 16)
    t = (gpio_data[3] ^ (gpio_data[19] >> 16)) & 0x0000FFFF; gpio_data[3] ^= t; gpio_data[19] ^= (t << 16)
    t = (gpio_data[4] ^ (gpio_data[20] >> 16)) & 0x0000FFFF; gpio_data[4] ^= t; gpio_data[20] ^= (t << 16)
    t = (gpio_data[5] ^ (gpio_data[21] >> 16)) & 0x0000FFFF; gpio_data[5] ^= t; gpio_data[21] ^= (t << 16)
    t = (gpio_data[6] ^ (gpio_data[22] >> 16)) & 0x0000FFFF; gpio_data[6] ^= t; gpio_data[22] ^= (t << 16)
    t = (gpio_data[7] ^ (gpio_data[23] >> 16)) & 0x0000FFFF; gpio_data[7] ^= t; gpio_data[23] ^= (t << 16)
    t = (gpio_data[8] ^ (gpio_data[24] >> 16)) & 0x0000FFFF; gpio_data[8] ^= t; gpio_data[24] ^= (t << 16)
    t = (gpio_data[9] ^ (gpio_data[25] >> 16)) & 0x0000FFFF; gpio_data[9] ^= t; gpio_data[25] ^= (t << 16)
    t = (gpio_data[10] ^ (gpio_data[26] >> 16)) & 0x0000FFFF; gpio_data[10] ^= t; gpio_data[26] ^= (t << 16)
    t = (gpio_data[11] ^ (gpio_data[27] >> 16)) & 0x0000FFFF; gpio_data[11] ^= t; gpio_data[27] ^= (t << 16)
    t = (gpio_data[12] ^ (gpio_data[28] >> 16)) & 0x0000FFFF; gpio_data[12] ^= t; gpio_data[28] ^= (t << 16)
    t = (gpio_data[13] ^ (gpio_data[29] >> 16)) & 0x0000FFFF; gpio_data[13] ^= t; gpio_data[29] ^= (t << 16)
    t = (gpio_data[14] ^ (gpio_data[30] >> 16)) & 0x0000FFFF; gpio_data[14] ^= t; gpio_data[30] ^= (t << 16)
    t = (gpio_data[15] ^ (gpio_data[31] >> 16)) & 0x0000FFFF; gpio_data[15] ^= t; gpio_data[31] ^= (t << 16)

    t = (gpio_data[0] ^ (gpio_data[8] >> 8)) & 0x00FF00FF; gpio_data[0] ^= t; gpio_data[8] ^= (t << 8)
    t = (gpio_data[1] ^ (gpio_data[9] >> 8)) & 0x00FF00FF; gpio_data[1] ^= t; gpio_data[9] ^= (t << 8)
    t = (gpio_data[2] ^ (gpio_data[10] >> 8)) & 0x00FF00FF; gpio_data[2] ^= t; gpio_data[10] ^= (t << 8)
    t = (gpio_data[3] ^ (gpio_data[11] >> 8)) & 0x00FF00FF; gpio_data[3] ^= t; gpio_data[11] ^= (t << 8)
    t = (gpio_data[4] ^ (gpio_data[12] >> 8)) & 0x00FF00FF; gpio_data[4] ^= t; gpio_data[12] ^= (t << 8)
    t = (gpio_data[5] ^ (gpio_data[13] >> 8)) & 0x00FF00FF; gpio_data[5] ^= t; gpio_data[13] ^= (t << 8)
    t = (gpio_data[6] ^ (gpio_data[14] >> 8)) & 0x00FF00FF; gpio_data[6] ^= t; gpio_data[14] ^= (t << 8)
    t = (gpio_data[7] ^ (gpio_data[15] >> 8)) & 0x00FF00FF; gpio_data[7] ^= t; gpio_data[15] ^= (t << 8)
    t = (gpio_data[16] ^ (gpio_data[24] >> 8)) & 0x00FF00FF; gpio_data[16] ^= t; gpio_data[24] ^= (t << 8)
    t = (gpio_data[17] ^ (gpio_data[25] >> 8)) & 0x00FF00FF; gpio_data[17] ^= t; gpio_data[25] ^= (t << 8)
    t = (gpio_data[18] ^ (gpio_data[26] >> 8)) & 0x00FF00FF; gpio_data[18] ^= t; gpio_data[26] ^= (t << 8)
    t = (gpio_data[19] ^ (gpio_data[27] >> 8)) & 0x00FF00FF; gpio_data[19] ^= t; gpio_data[27] ^= (t << 8)
    t = (gpio_data[20] ^ (gpio_data[28] >> 8)) & 0x00FF00FF; gpio_data[20] ^= t; gpio_data[28] ^= (t << 8)
    t = (gpio_data[21] ^ (gpio_data[29] >> 8)) & 0x00FF00FF; gpio_data[21] ^= t; gpio_data[29] ^= (t << 8)
    t = (gpio_data[22] ^ (gpio_data[30] >> 8)) & 0x00FF00FF; gpio_data[22] ^= t; gpio_data[30] ^= (t << 8)
    t = (gpio_data[23] ^ (gpio_data[31] >> 8)) & 0x00FF00FF; gpio_data[23] ^= t; gpio_data[31] ^= (t << 8)

    t = (gpio_data[0] ^ (gpio_data[4] >> 4)) & 0x0F0F0F0F; gpio_data[0] ^= t; gpio_data[4] ^= (t << 4)
    t = (gpio_data[1] ^ (gpio_data[5] >> 4)) & 0x0F0F0F0F; gpio_data[1] ^= t; gpio_data[5] ^= (t << 4)
    t = (gpio_data[2] ^ (gpio_data[6] >> 4)) & 0x0F0F0F0F; gpio_data[2] ^= t; gpio_data[6] ^= (t << 4)
    t = (gpio_data[3] ^ (gpio_data[7] >> 4)) & 0x0F0F0F0F; gpio_data[3] ^= t; gpio_data[7] ^= (t << 4)
    t = (gpio_data[8] ^ (gpio_data[12] >> 4)) & 0x0F0F0F0F; gpio_data[8] ^= t; gpio_data[12] ^= (t << 4)
    t = (gpio_data[9] ^ (gpio_data[13] >> 4)) & 0x0F0F0F0F; gpio_data[9] ^= t; gpio_data[13] ^= (t << 4)
    t = (gpio_data[10] ^ (gpio_data[14] >> 4)) & 0x0F0F0F0F; gpio_data[10] ^= t; gpio_data[14] ^= (t << 4)
    t = (gpio_data[11] ^ (gpio_data[15] >> 4)) & 0x0F0F0F0F; gpio_data[11] ^= t; gpio_data[15] ^= (t << 4)
    t = (gpio_data[16] ^ (gpio_data[20] >> 4)) & 0x0F0F0F0F; gpio_data[16] ^= t; gpio_data[20] ^= (t << 4)
    t = (gpio_data[17] ^ (gpio_data[21] >> 4)) & 0x0F0F0F0F; gpio_data[17] ^= t; gpio_data[21] ^= (t << 4)
    t = (gpio_data[18] ^ (gpio_data[22] >> 4)) & 0x0F0F0F0F; gpio_data[18] ^= t; gpio_data[22] ^= (t << 4)
    t = (gpio_data[19] ^ (gpio_data[23] >> 4)) & 0x0F0F0F0F; gpio_data[19] ^= t; gpio_data[23] ^= (t << 4)
    t = (gpio_data[24] ^ (gpio_data[28] >> 4)) & 0x0F0F0F0F; gpio_data[24] ^= t; gpio_data[28] ^= (t << 4)
    t = (gpio_data[25] ^ (gpio_data[29] >> 4)) & 0x0F0F0F0F; gpio_data[25] ^= t; gpio_data[29] ^= (t << 4)
    t = (gpio_data[26] ^ (gpio_data[30] >> 4)) & 0x0F0F0F0F; gpio_data[26] ^= t; gpio_data[30] ^= (t << 4)
    t = (gpio_data[27] ^ (gpio_data[31] >> 4)) & 0x0F0F0F0F; gpio_data[27] ^= t; gpio_data[31] ^= (t << 4)

    t = (gpio_data[0] ^ (gpio_data[2] >> 2)) & 0x33333333; gpio_data[0] ^= t; gpio_data[2] ^= (t << 2)
    t = (gpio_data[1] ^ (gpio_data[3] >> 2)) & 0x33333333; gpio_data[1] ^= t; gpio_data[3] ^= (t << 2)
    t = (gpio_data[4] ^ (gpio_data[6] >> 2)) & 0x33333333; gpio_data[4] ^= t; gpio_data[6] ^= (t << 2)
    t = (gpio_data[5] ^ (gpio_data[7] >> 2)) & 0x33333333; gpio_data[5] ^= t; gpio_data[7] ^= (t << 2)
    t = (gpio_data[8] ^ (gpio_data[10] >> 2)) & 0x33333333; gpio_data[8] ^= t; gpio_data[10] ^= (t << 2)
    t = (gpio_data[9] ^ (gpio_data[11] >> 2)) & 0x33333333; gpio_data[9] ^= t; gpio_data[11] ^= (t << 2)
    t = (gpio_data[12] ^ (gpio_data[14] >> 2)) & 0x33333333; gpio_data[12] ^= t; gpio_data[14] ^= (t << 2)
    t = (gpio_data[13] ^ (gpio_data[15] >> 2)) & 0x33333333; gpio_data[13] ^= t; gpio_data[15] ^= (t << 2)
    t = (gpio_data[16] ^ (gpio_data[18] >> 2)) & 0x33333333; gpio_data[16] ^= t; gpio_data[18] ^= (t << 2)
    t = (gpio_data[17] ^ (gpio_data[19] >> 2)) & 0x33333333; gpio_data[17] ^= t; gpio_data[19] ^= (t << 2)
    t = (gpio_data[20] ^ (gpio_data[22] >> 2)) & 0x33333333; gpio_data[20] ^= t; gpio_data[22] ^= (t << 2)
    t = (gpio_data[21] ^ (gpio_data[23] >> 2)) & 0x33333333; gpio_data[21] ^= t; gpio_data[23] ^= (t << 2)
    t = (gpio_data[24] ^ (gpio_data[26] >> 2)) & 0x33333333; gpio_data[24] ^= t; gpio_data[26] ^= (t << 2)
    t = (gpio_data[25] ^ (gpio_data[27] >> 2)) & 0x33333333; gpio_data[25] ^= t; gpio_data[27] ^= (t << 2)
    t = (gpio_data[28] ^ (gpio_data[30] >> 2)) & 0x33333333; gpio_data[28] ^= t; gpio_data[30] ^= (t << 2)
    t = (gpio_data[29] ^ (gpio_data[31] >> 2)) & 0x33333333; gpio_data[29] ^= t; gpio_data[31] ^= (t << 2)

    m = 0x55555555
    t = (gpio_data[0] ^ (gpio_data[1] >> 1)) & 0x55555555; gpio_data[0] ^= t; gpio_data[1] ^= (t << 1)
    t = (gpio_data[2] ^ (gpio_data[3] >> 1)) & 0x55555555; gpio_data[2] ^= t; gpio_data[3] ^= (t << 1)
    t = (gpio_data[4] ^ (gpio_data[5] >> 1)) & 0x55555555; gpio_data[4] ^= t; gpio_data[5] ^= (t << 1)
    t = (gpio_data[6] ^ (gpio_data[7] >> 1)) & 0x55555555; gpio_data[6] ^= t; gpio_data[7] ^= (t << 1)
    t = (gpio_data[8] ^ (gpio_data[9] >> 1)) & 0x55555555; gpio_data[8] ^= t; gpio_data[9] ^= (t << 1)
    t = (gpio_data[10] ^ (gpio_data[11] >> 1)) & 0x55555555; gpio_data[10] ^= t; gpio_data[11] ^= (t << 1)
    t = (gpio_data[12] ^ (gpio_data[13] >> 1)) & 0x55555555; gpio_data[12] ^= t; gpio_data[13] ^= (t << 1)
    t = (gpio_data[14] ^ (gpio_data[15] >> 1)) & 0x55555555; gpio_data[14] ^= t; gpio_data[15] ^= (t << 1)
    t = (gpio_data[16] ^ (gpio_data[17] >> 1)) & 0x55555555; gpio_data[16] ^= t; gpio_data[17] ^= (t << 1)
    t = (gpio_data[18] ^ (gpio_data[19] >> 1)) & 0x55555555; gpio_data[18] ^= t; gpio_data[19] ^= (t << 1)
    t = (gpio_data[20] ^ (gpio_data[21] >> 1)) & 0x55555555; gpio_data[20] ^= t; gpio_data[21] ^= (t << 1)
    t = (gpio_data[22] ^ (gpio_data[23] >> 1)) & 0x55555555; gpio_data[22] ^= t; gpio_data[23] ^= (t << 1)
    t = (gpio_data[24] ^ (gpio_data[25] >> 1)) & 0x55555555; gpio_data[24] ^= t; gpio_data[25] ^= (t << 1)
    t = (gpio_data[26] ^ (gpio_data[27] >> 1)) & 0x55555555; gpio_data[26] ^= t; gpio_data[27] ^= (t << 1)
    t = (gpio_data[28] ^ (gpio_data[29] >> 1)) & 0x55555555; gpio_data[28] ^= t; gpio_data[29] ^= (t << 1)
    t = (gpio_data[30] ^ (gpio_data[31] >> 1)) & 0x55555555; gpio_data[30] ^= t; gpio_data[31] ^= (t << 1)
    ##formatter:on


class TestMemoryUtils(unittest.TestCase):
    def test_transpose(self):
        gpio_data = [
            0b00100000000000000000000000000001,  # 0
            0b00100000000000000000000000000001,  # 1
            0b00100000000000000000000000000001,  # 2
            0b00100000000000000000000000000001,  # 3
            0b00100000000000000000000000000001,  # 4
            0b00100000000000000000000000000001,  # 5
            0b00100000000000000000000000000001,  # 6
            0b00100000000000000000000000000001,  # 7
            0b00100000000000000000000000000001,  # 8
            0b00100000000000000000000000000001,  # 9
            0b00100000000000000000000000000001,  # 10
            0b00100000000000000000000000000001,  # 11
            0b00100000000000000000000000000001,  # 12
            0b00100000000000000000000000000001,  # 13
            0b00100000000000000000000000000001,  # 14
            0b00100000000000000000000000000001,  # 15
            0b00100000000000000000000000000001,  # 16
            0b00100000000000000000000000000001,  # 17
            0b00100000000000000000000000000001,  # 18
            0b00100000000000000000000000000001,  # 19
            0b00100000000000000000000000000001,  # 20
            0b00100000000000000000000000000001,  # 21
            0b00100000000000000000000000000001,  # 22
            0b00100000000000000000000000000001,  # 23
            0b00100000000000000000000000000001,  # 24
            0b00100000000000000000000000000001,  # 25
            0b00100000000000000000000000000001,  # 26
            0b00100000000000000000000000000001,  # 27
            0b00100000000000000000000000000001,  # 28
            0b00100000000000000000000000000001,  # 29
            0b00100000000000000000000000000001,  # 30
            0b00100000000000000000000000000001  # 31
        ]

        t0 = int(time.time() * 1000)
        for i in range(165):
            transpose32(gpio_data)
        t1 = int(time.time() * 1000)
        print("transpose:" + str(t1 - t0))

    pass


if __name__ == '__main__':
    unittest.main()
