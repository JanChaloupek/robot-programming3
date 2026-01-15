# neopixel.py – stub for CircuitPython NeoPixel library (VS Code / Pylance)

import board
import digitalio

# Pixel order constants
RGB = "RGB"
GRB = "GRB"
RGBW = "RGBW"
GRBW = "GRBW"

# Dummy replacement for neopixel_write
def neopixel_write(pin, buf):
    pass

# Dummy replacement for adafruit_pixelbuf.PixelBuf
class _PixelBuf:
    def __init__(self, n, *, brightness=1.0, byteorder="GRB", auto_write=True):
        self._n = n
        self.brightness = brightness
        self.auto_write = auto_write
        self.byteorder = byteorder
        self._pixels = [(0, 0, 0)] * n

    def __len__(self):
        return self._n

    def __getitem__(self, index):
        return self._pixels[index]

    def __setitem__(self, index, value):
        self._pixels[index] = value
        if self.auto_write:
            self.show()

    def fill(self, color):
        self._pixels = [color] * self._n
        if self.auto_write:
            self.show()

    def show(self):
        pass


class NeoPixel(_PixelBuf):
    def __init__(
        self,
        pin,
        n,
        *,
        bpp=3,
        brightness=1.0,
        auto_write=True,
        pixel_order=None
    ):
        if pixel_order is None:
            pixel_order = GRB if bpp == 3 else GRBW

        super().__init__(
            n,
            brightness=brightness,
            byteorder=pixel_order,
            auto_write=auto_write,
        )

        self.pin = digitalio.DigitalInOut(pin)
        self.pin.direction = digitalio.Direction.OUTPUT
        self._power = None

    def deinit(self):
        self.fill(0)
        self.show()
        self.pin = None
        self._power = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        self.deinit()

    @property
    def n(self):
        return len(self)

    def write(self):
        # Deprecated alias for show()
        self.show()

    def _transmit(self, buffer):
        neopixel_write(self.pin, buffer)
