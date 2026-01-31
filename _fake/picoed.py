"""
Fake implementace CircuitPython modulu `picoed`.

Simuluje:
- I2C sběrnice
- LED displej (17×7)
- tlačítka
- stavovou LED
- hudební výstup

Vše je deterministické a vhodné pro unit testy.
"""

import busio
import board
import digitalio


# ---------------------------------------------------------
# Fake Image
# ---------------------------------------------------------

class Image:
    """Fake verze picoed.display.Image."""

    NO = b"\x00\x00\x00\x00\x00\x41\x22\x14\x08\x14\x22\x41\x00\x00\x00\x00\x00"
    SQUARE = b"\x00\x00\x00\x00\x00\x00\x3E\x22\x22\x22\x3E\x00\x00\x00\x00\x00\x00"
    RECTANGLE = b"\xFF\x41\x41\x41\x41\x41\x41\x41\x41\x41\x41\x41\x41\x41\x41\x41\xFF"
    RHOMBUS = b"\x00\x00\x00\x00\x00\x08\x14\x22\x41\x22\x14\x08\x00\x00\x00\x00\x00"
    TARGET = b"\x00\x00\x00\x00\x00\x08\x1C\x36\x63\x36\x1C\x08\x00\x00\x00\x00\x00"
    CHESSBOARD = b"\x2A\x55\x2A\x55\x2A\x55\x2A\x55\x2A\x55\x2A\x55\x2A\x55\x2A\x55\x2A"
    HAPPY = b"\x00\x00\x00\x00\x10\x20\x46\x40\x40\x40\x46\x20\x10\x00\x00\x00\x00"
    SAD = b"\x00\x00\x00\x00\x40\x22\x12\x10\x10\x10\x12\x22\x40\x00\x00\x00\x00"
    YES = b"\x00\x00\x00\x00\x00\x00\x08\x10\x20\x10\x08\x04\x02\x00\x00\x00\x00"
    HEART = b"\x00\x00\x00\x00\x00\x0E\x1F\x3F\x7E\x3F\x1F\x0E\x00\x00\x00\x00\x00"
    TRIANGLE = b"\x00\x00\x40\x60\x50\x48\x44\x42\x41\x42\x44\x48\x50\x60\x40\x00\x00"
    CHAGRIN = b"\x00\x00\x00\x00\x22\x14\x08\x40\x40\x40\x08\x14\x22\x00\x00\x00\x00"
    SMILING_FACE = b"\x00\x00\x00\x00\x00\x06\x36\x50\x50\x50\x36\x06\x00\x00\x00\x00\x00"
    CRY = b"\x60\x70\x70\x38\x02\x02\x64\x50\x50\x50\x64\x02\x02\x38\x70\x70\x60"
    DOWNCAST = b"\x00\x00\x00\x02\x0A\x11\x08\x40\x40\x40\x08\x11\x0A\x02\x00\x00\x00"
    LOOK_RIGHT = b"\x00\x00\x00\x00\x00\x00\x00\x26\x2F\x06\x00\x06\x0F\x06\x00\x00\x00"
    LOOK_LEFT = b"\x00\x00\x00\x06\x0F\x06\x00\x06\x2F\x26\x00\x00\x00\x00\x00\x00\x00"
    TONGUE = b"\x00\x00\x00\x00\x04\x12\x14\x70\x70\x70\x16\x16\x00\x00\x00\x00\x00"
    PEEK_RIGHT = b"\x00\x00\x04\x04\x04\x0C\x0C\x40\x40\x40\x04\x04\x04\x0C\x0C\x00\x00"
    PEEK_LEFT = b"\x00\x00\x0C\x0C\x04\x04\x04\x40\x40\x40\x0C\x0C\x04\x04\x04\x00\x00"
    TEAR_EYES = b"\x00\x00\x00\x06\x7F\x06\x20\x40\x40\x40\x20\x06\x7F\x06\x00\x00\x00"
    PROUD = b"\x01\x07\x0F\x0F\x0F\x0F\x47\x41\x41\x41\x27\x0F\x0F\x0F\x0F\x07\x01"
    SNEER_LEFT = b"\x00\x00\x00\x0C\x08\x0C\x2C\x40\x40\x40\x2C\x08\x0C\x0C\x00\x00\x00"
    SNEER_RIGHT = b"\x00\x00\x00\x0C\x0C\x08\x2C\x40\x40\x40\x2C\x0C\x08\x0C\x00\x00\x00"
    SUPERCILIOUS_LOOK = b"\x00\x00\x00\x0E\x0C\x0E\x00\x20\x20\x20\x00\x0E\x0C\x0E\x00\x00\x00"
    EXCITED = b"\x60\x70\x70\x3E\x01\x06\x30\x50\x50\x50\x30\x06\x01\x3E\x70\x70\x60"

    def __new__(cls, value=None):
        if value is not None and isinstance(value, str):
            data = []
            for y in range(7):
                if y < 6 and value[(y + 1) * 18 - 1] != ":":
                    raise ValueError("Each line must end with ':'")
                for x in range(17):
                    data.append([x, y, int(value[y * 18 + x])])
            return data
        return [[0, 0, 0]]


# ---------------------------------------------------------
# Fake Display
# ---------------------------------------------------------

class Display:
    width = 17
    height = 7

    def __init__(self, i2c=None):
        self._i2c = i2c
        self.buffer = [[0] * self.width for _ in range(self.height)]
        self.last_scrolled = None
        self.last_brightness = None

    @staticmethod
    def pixel_addr(x, y):
        if x > 8:
            x = 17 - x
            y += 8
        else:
            y = 7 - y
        return x * 16 + y

    def clear(self):
        for y in range(self.height):
            for x in range(self.width):
                self.buffer[y][x] = 0

    def _set_pixel(self, x, y, brightness):
        if 0 <= x < self.width and 0 <= y < self.height:
            self.buffer[y][x] = max(0, min(255, int(brightness)))

    def scroll(self, value, brightness=30):
        self.last_scrolled = str(value)
        self.last_brightness = max(0, min(255, int(brightness)))

    def show(self, value, brightness=30):
        b = max(0, min(255, int(brightness)))
        self.last_brightness = b

        if isinstance(value, (int, float, str)):
            self.scroll(value, b)

        elif isinstance(value, (bytes, bytearray)):
            cols = list(value)
            for x in range(min(self.width, len(cols))):
                col = cols[x]
                for y in range(self.height):
                    bit = (col >> y) & 1
                    self._set_pixel(x, y, b if bit else 0)

        else:
            self.clear()
            for x, y, v in value:
                self._set_pixel(x, y, int(v * 255 / 9))


# ---------------------------------------------------------
# Fake LED
# ---------------------------------------------------------

class Led:
    def __init__(self, pin):
        self._pin = pin
        self._io = None
        self.state_history = []

    def _init(self):
        if not self._io:
            self._io = digitalio.DigitalInOut(self._pin)
            self._io.direction = digitalio.Direction.OUTPUT

    def deinit(self):
        if self._io:
            self._io.deinit()
            self._io = None

    def on(self):
        self._init()
        self._io.value = True
        self.state_history.append(True)

    def off(self):
        self._init()
        self._io.value = False
        self.state_history.append(False)

    def toggle(self):
        self._init()
        new = not self._io.value
        self._io.value = new
        self.state_history.append(new)


# ---------------------------------------------------------
# Fake Button
# ---------------------------------------------------------

class Button:
    def __init__(self, pin):
        self._pin = digitalio.DigitalInOut(pin)
        self._pin.direction = digitalio.Direction.INPUT
        self._pin.pull = digitalio.Pull.UP
        self._last_pressed = False
        self._fake_value = True

    def set_pressed(self, pressed: bool):
        self._fake_value = not pressed

    @property
    def value(self):
        return self._fake_value

    def is_pressed(self):
        return not self.value

    def was_pressed(self):
        if not self.value and not self._last_pressed:
            self._last_pressed = True
            return True
        if self.value:
            self._last_pressed = False
        return False


# ---------------------------------------------------------
# Fake Music
# ---------------------------------------------------------

class Music:
    def __init__(self, pin):
        self.pin = pin
        self.history = []
        self.last_frequency = None
        self.last_duration = None
        self.playing = False

    def play(self, melody, wait=True, loop=False):
        self.history.append(("play", melody, wait, loop))
        self.playing = True

    def pitch(self, frequency, duration=None):
        self.history.append(("pitch", frequency, duration))
        self.last_frequency = frequency
        self.last_duration = duration
        self.playing = True

    def tone(self, frequency, duration=None):
        self.pitch(frequency, duration)

    def stop(self):
        self.history.append(("stop",))
        self.playing = False

    def reset(self):
        self.history.append(("reset",))
        self.playing = False
        self.last_frequency = None
        self.last_duration = None


# ---------------------------------------------------------
# Modulové instance
# ---------------------------------------------------------

i2c = busio.I2C(board.SCL, board.SDA)

try:
    internal_i2c = busio.I2C(board.I2C0_SCL, board.I2C0_SDA)
    display = Display(internal_i2c)
except Exception:
    internal_i2c = None
    display = Display(i2c)

button_a = Button(board.BUTTON_A)
button_b = Button(board.BUTTON_B)
led = Led(board.LED)
music = Music(board.BUZZER)
