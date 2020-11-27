from abc import ABCMeta, abstractmethod


class FrameProducer:
    __metaclass__ = ABCMeta

    @abstractmethod
    def get_frame(self):
        pass

    @abstractmethod
    def init(self, frame_rate: int, num_strips: int, leds_per_strip: int):
        pass
