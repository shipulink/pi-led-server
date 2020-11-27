import math

from app.frame_producer import FrameProducer


class ColorSweep(FrameProducer):
    def __init__(self, cycle_duration_seconds: int):
        self.cycle_duration_seconds = cycle_duration_seconds
        self.initialized = False
        self.num_strips = None
        self.leds_per_strip = None
        self.cycle_length = None
        self.rgb_data = None
        self.i = 0

    def init(self, frame_rate: int, num_strips: int, leds_per_strip: int):
        cycle_length_one_third = int((self.cycle_duration_seconds * frame_rate) / 3)
        cycle_length_two_thirds = cycle_length_one_third * 2
        cycle_length = cycle_length_one_third * 3
        shared_sin_wave_ints = [0] * cycle_length_two_thirds
        i = 0
        while i < len(shared_sin_wave_ints):
            shared_sin_wave_ints[i] = int((math.sin(i * math.pi / cycle_length_one_third - math.pi / 2) + 1) * 255 / 2)
            i += 1

        rgb_data = []
        i = 0
        while i < cycle_length:
            rgb = [0] * 3
            if i < cycle_length_one_third:
                rgb[0] = shared_sin_wave_ints[cycle_length_one_third + i]
            if i >= cycle_length_two_thirds:
                rgb[0] = shared_sin_wave_ints[i - cycle_length_two_thirds]
            if i < cycle_length_two_thirds:
                rgb[1] = shared_sin_wave_ints[i]
            if i >= cycle_length_one_third:
                rgb[2] = shared_sin_wave_ints[i - cycle_length_one_third]
            rgb_data.append(bytes(rgb))
            i += 1

        self.num_strips = num_strips
        self.leds_per_strip = leds_per_strip
        self.cycle_length = cycle_length
        self.rgb_data = rgb_data
        self.initialized = True

    def get_frame(self):
        if not self.initialized:
            raise Exception("ColorSweep frame producer has not been initialized")

        current_color = self.rgb_data[self.i]
        self.i += 1
        if self.i >= self.cycle_length:
            self.i = 0
        single_strip_frame = [current_color] * self.leds_per_strip
        return [single_strip_frame] * self.num_strips
