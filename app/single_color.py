from app.frame_producer import FrameProducer


class SingleColor(FrameProducer):
    def __init__(self, color: str):
        invalid_color_error = "Invalid color string. Must be a hex color string. E.g.: ffff00 (yellow)"

        try:
            self.color = bytes.fromhex(color)
        except ValueError:
            raise Exception(invalid_color_error)

        if not len(self.color) == 3:
            raise Exception(invalid_color_error)

        self.initialized = False
        self.num_strips = None
        self.leds_per_strip = None

    def init(self, frame_rate: int, num_strips: int, leds_per_strip: int):
        self.num_strips = num_strips
        self.leds_per_strip = leds_per_strip
        self.initialized = True

    def get_frame(self):
        if not self.initialized:
            raise Exception("SingleColor frame producer has not been initialized")

        single_strip_frame = [self.color] * self.leds_per_strip
        return [single_strip_frame] * self.num_strips
