import time
from queue import Queue
from threading import Thread
from threading import Timer

from app.color_sweep import ColorSweep
from app.frame_producer import FrameProducer
from app.gpio import GpioInfo
from app.neopixel_driver import NeopixelDriver


# TODO: Change to accept different effects for each strip
def play_animation(
        frame_producer: FrameProducer,
        frames_per_second: int,
        leds_per_strip: int,
        gpio_pins: [GpioInfo],
        duration_seconds: int
):
    frame_producer.init(frames_per_second, len(gpio_pins), leds_per_strip)
    frame_buffer = Queue(frames_per_second)  # buffer up to one second's worth of frames
    playing = [True]

    def fill_buffer():
        while playing[0]:
            frame_buffer.put(frame_producer.get_frame())

    thread_fill_buffer = Thread(target=fill_buffer)
    thread_fill_buffer.start()

    driver = NeopixelDriver(leds_per_strip, gpio_pins)
    driver.start()

    def play():
        while playing[0]:
            driver.send_frame(frame_buffer.get())
            time.sleep(1 / frames_per_second)
        driver.stop()
        # The frame-buffering thread cannot exit until frame_buffer is empty
        while not frame_buffer.empty():
            frame_buffer.get()

    thread_play = Thread(target=play)
    thread_play.start()

    def stop(is_playing: []):
        is_playing[0] = False

    stop_timer = Timer(duration_seconds, stop, [playing])
    stop_timer.start()
    thread_play.join()
    thread_fill_buffer.join()


color_sweep_producer = ColorSweep(2)
play_animation(color_sweep_producer, 30, 220, [GpioInfo(18)], 5)

# single_color_producer = SingleColor("ffff00")    # yellow
# single_color_producer = SingleColor("eb34d2")    # pink
# single_color_producer = SingleColor("000000")    # black
# single_color_producer = SingleColor("ffffff")    # white
# play_animation(single_color_producer, 5, 4, [GpioInfo(18)], 2)
