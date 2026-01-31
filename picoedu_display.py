import time
from adafruit_bus_device.i2c_device import I2CDevice

_MODE_REGISTER = 0x00
_FRAME_REGISTER = 0x01
_BLINK_REGISTER = 0x05
_AUDIOSYNC_REGISTER = 0x06
_SHUTDOWN_REGISTER = 0x0A

_CONFIG_BANK = 0x0B
_BANK_ADDRESS = 0xFD

_PICTURE_MODE = 0x00

_ENABLE_OFFSET = 0x00
_BLINK_OFFSET = 0x12
_COLOR_OFFSET = 0x24


class PicoEduDisplay:
    width = 17
    height = 7

    def __init__(self, i2c, address=0x74):
        self.i2c_device = I2CDevice(i2c, address)
        self.address = address
        self._frame = 0
        self.reset()
        self.init()

    # -----------------------------
    # Low-level I2C helpers
    # -----------------------------
    def _bank(self, bank):
        with self.i2c_device as i2c:
            i2c.write(bytes([_BANK_ADDRESS, bank]))

    def _register(self, bank, register, value):
        self._bank(bank)
        with self.i2c_device as i2c:
            i2c.write(bytes([register, value]))

    # -----------------------------
    # Device control
    # -----------------------------
    def reset(self):
        self.sleep(True)
        time.sleep(0.001)
        self.sleep(False)

    def sleep(self, value):
        self._register(_CONFIG_BANK, _SHUTDOWN_REGISTER, 0 if value else 1)

    def init(self):
        self._register(_CONFIG_BANK, _MODE_REGISTER, _PICTURE_MODE)
        self.frame(0)

        # Enable all LEDs in all frames
        for frame in range(8):
            self.fill(0, frame=frame)
            for col in range(18):
                self._register(frame, _ENABLE_OFFSET + col, 0xFF)

        self._register(_CONFIG_BANK, _AUDIOSYNC_REGISTER, 0)

    def frame(self, frame):
        self._frame = frame
        self._register(_CONFIG_BANK, _FRAME_REGISTER, frame)

    # -----------------------------
    # Drawing
    # -----------------------------
    def fill(self, color, frame=None):
        if frame is None:
            frame = self._frame

        self._bank(frame)
        data = bytes([color] * 24)

        with self.i2c_device as i2c:
            for row in range(6):
                i2c.write(bytes([_COLOR_OFFSET + row * 24]) + data)

    def write_frame(self, data, frame=None):
        if frame is None:
            frame = self._frame

        self._bank(frame)
        with self.i2c_device as i2c:
            i2c.write(bytes([_COLOR_OFFSET]) + bytes(data))

    # -----------------------------
    # Pixel mapping for Pico:ed
    # -----------------------------
    def _pixel_addr(self, x, y):
        if x > 8:
            x = 17 - x
            y += 8
        else:
            y = 7 - y
        return x * 16 + y

    def pixel(self, x, y, color):
        if not (0 <= x < self.width and 0 <= y < self.height):
            return

        pixel = self._pixel_addr(x, y)
        self._register(self._frame, _COLOR_OFFSET + pixel, color)
