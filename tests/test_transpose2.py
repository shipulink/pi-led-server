import time
import unittest


# import app.dma as dma


# import app.memory_utils as mu


def build_mock_rgb_data(lights_per_strip: int, num_strips: int):
    component = int(0b01000000)
    rgb = [0] * 3
    rgb[0] = component
    rgb[1] = component
    rgb[2] = component
    rgb_bytes = bytes(rgb)
    rgb_data_for_one_strip = [rgb_bytes] * 2
    return [rgb_data_for_one_strip] * 32


def transform_rgb_data_to_words_array(rgb_data):
    return 0


def swap(a0, a1, j, m):
    t = (a0 ^ (a1 >> j)) & m
    return a0 ^ t, a1 ^ (t << j)


def transpose32():
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

    a0 = gpio_data[0]
    a1 = gpio_data[1]
    a2 = gpio_data[2]
    a3 = gpio_data[3]
    a4 = gpio_data[4]
    a5 = gpio_data[5]
    a6 = gpio_data[6]
    a7 = gpio_data[7]
    a8 = gpio_data[8]
    a9 = gpio_data[9]
    a10 = gpio_data[10]
    a11 = gpio_data[11]
    a12 = gpio_data[12]
    a13 = gpio_data[13]
    a14 = gpio_data[14]
    a15 = gpio_data[15]
    a16 = gpio_data[16]
    a17 = gpio_data[17]
    a18 = gpio_data[18]
    a19 = gpio_data[19]
    a20 = gpio_data[20]
    a21 = gpio_data[21]
    a22 = gpio_data[22]
    a23 = gpio_data[23]
    a24 = gpio_data[24]
    a25 = gpio_data[25]
    a26 = gpio_data[26]
    a27 = gpio_data[27]
    a28 = gpio_data[28]
    a29 = gpio_data[29]
    a30 = gpio_data[30]
    a31 = gpio_data[31]

    m = 0x0000FFFF
    a0, a16 = swap(a0, a16, 16, m)
    a1, a17 = swap(a1, a17, 16, m)
    a2, a18 = swap(a2, a18, 16, m)
    a3, a19 = swap(a3, a19, 16, m)
    a4, a20 = swap(a4, a20, 16, m)
    a5, a21 = swap(a5, a21, 16, m)
    a6, a22 = swap(a6, a22, 16, m)
    a7, a23 = swap(a7, a23, 16, m)
    a8, a24 = swap(a8, a24, 16, m)
    a9, a25 = swap(a9, a25, 16, m)
    a10, a26 = swap(a10, a26, 16, m)
    a11, a27 = swap(a11, a27, 16, m)
    a12, a28 = swap(a12, a28, 16, m)
    a13, a29 = swap(a13, a29, 16, m)
    a14, a30 = swap(a14, a30, 16, m)
    a15, a31 = swap(a15, a31, 16, m)

    m = 0x00FF00FF
    a0, a8 = swap(a0, a8, 8, m)
    a1, a9 = swap(a1, a9, 8, m)
    a2, a10 = swap(a2, a10, 8, m)
    a3, a11 = swap(a3, a11, 8, m)
    a4, a12 = swap(a4, a12, 8, m)
    a5, a13 = swap(a5, a13, 8, m)
    a6, a14 = swap(a6, a14, 8, m)
    a7, a15 = swap(a7, a15, 8, m)
    a16, a24 = swap(a16, a24, 8, m)
    a17, a25 = swap(a17, a25, 8, m)
    a18, a26 = swap(a18, a26, 8, m)
    a19, a27 = swap(a19, a27, 8, m)
    a20, a28 = swap(a20, a28, 8, m)
    a21, a29 = swap(a21, a29, 8, m)
    a22, a30 = swap(a22, a30, 8, m)
    a23, a31 = swap(a23, a31, 8, m)

    m = 0x0F0F0F0F
    a0, a4 = swap(a0, a4, 4, m)
    a1, a5 = swap(a1, a5, 4, m)
    a2, a6 = swap(a2, a6, 4, m)
    a3, a7 = swap(a3, a7, 4, m)
    a8, a12 = swap(a8, a12, 4, m)
    a9, a13 = swap(a9, a13, 4, m)
    a10, a14 = swap(a10, a14, 4, m)
    a11, a15 = swap(a11, a15, 4, m)
    a16, a20 = swap(a16, a20, 4, m)
    a17, a21 = swap(a17, a21, 4, m)
    a18, a22 = swap(a18, a22, 4, m)
    a19, a23 = swap(a19, a23, 4, m)
    a24, a28 = swap(a24, a28, 4, m)
    a25, a29 = swap(a25, a29, 4, m)
    a26, a30 = swap(a26, a30, 4, m)
    a27, a31 = swap(a27, a31, 4, m)

    m = 0x33333333
    a0, a2 = swap(a0, a2, 2, m)
    a1, a3 = swap(a1, a3, 2, m)
    a4, a6 = swap(a4, a6, 2, m)
    a5, a7 = swap(a5, a7, 2, m)
    a8, a10 = swap(a8, a10, 2, m)
    a9, a11 = swap(a9, a11, 2, m)
    a12, a14 = swap(a12, a14, 2, m)
    a13, a15 = swap(a13, a15, 2, m)
    a16, a18 = swap(a16, a18, 2, m)
    a17, a19 = swap(a17, a19, 2, m)
    a20, a22 = swap(a20, a22, 2, m)
    a21, a23 = swap(a21, a23, 2, m)
    a24, a26 = swap(a24, a26, 2, m)
    a25, a27 = swap(a25, a27, 2, m)
    a28, a30 = swap(a28, a30, 2, m)
    a29, a31 = swap(a29, a31, 2, m)

    m = 0x55555555
    a0, a1 = swap(a0, a1, 1, m)
    a2, a3 = swap(a2, a3, 1, m)
    a4, a5 = swap(a4, a5, 1, m)
    a6, a7 = swap(a6, a7, 1, m)
    a8, a9 = swap(a8, a9, 1, m)
    a10, a11 = swap(a10, a11, 1, m)
    a12, a13 = swap(a12, a13, 1, m)
    a14, a15 = swap(a14, a15, 1, m)
    a16, a17 = swap(a16, a17, 1, m)
    a18, a19 = swap(a18, a19, 1, m)
    a20, a21 = swap(a20, a21, 1, m)
    a22, a23 = swap(a22, a23, 1, m)
    a24, a25 = swap(a24, a25, 1, m)
    a26, a27 = swap(a26, a27, 1, m)
    a28, a29 = swap(a28, a29, 1, m)
    a30, a31 = swap(a30, a31, 1, m)

    gpio_data[0] = a0
    gpio_data[1] = a1
    gpio_data[2] = a2
    gpio_data[3] = a3
    gpio_data[4] = a4
    gpio_data[5] = a5
    gpio_data[6] = a6
    gpio_data[7] = a7
    gpio_data[8] = a8
    gpio_data[9] = a9
    gpio_data[10] = a10
    gpio_data[11] = a11
    gpio_data[12] = a12
    gpio_data[13] = a13
    gpio_data[14] = a14
    gpio_data[15] = a15
    gpio_data[16] = a16
    gpio_data[17] = a17
    gpio_data[18] = a18
    gpio_data[19] = a19
    gpio_data[20] = a20
    gpio_data[21] = a21
    gpio_data[22] = a22
    gpio_data[23] = a23
    gpio_data[24] = a24
    gpio_data[25] = a25
    gpio_data[26] = a26
    gpio_data[27] = a27
    gpio_data[28] = a28
    gpio_data[29] = a29
    gpio_data[30] = a30
    gpio_data[31] = a31


class TestMemoryUtils(unittest.TestCase):
    def test_transpose(self):
        t0 = int(time.time() * 1000)
        for i in range(165):
            transpose32()
        t1 = int(time.time() * 1000)
        print("transpose:" + str(t1 - t0))

    pass


if __name__ == '__main__':
    unittest.main()
