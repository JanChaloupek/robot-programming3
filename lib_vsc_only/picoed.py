"""
picoed.py – společný stub pro VS Code a fake hardware pro testy.

Tento modul napodobuje CircuitPython modul `picoed`, který poskytuje
předpřipravené instance zařízení na desce pico:ed:

- i2c        – I2C sběrnice
- display    – LED displej
- button_a   – levé tlačítko
- button_b   – pravé tlačítko
- led        – stavová LED
- music      – zvukový výstup

V této fake verzi:
- všechny objekty jsou simulované
- I2C používá busio.I2C
- display ukládá pixely do bufferu
- tlačítka mají simulovaný stav
- LED má stav True/False
- vše je deterministické a testovatelné
"""

import board
from busio import I2C


# ---------------------------------------------------------
# I2C sběrnice (jediná implementace z busio.I2C)
# ---------------------------------------------------------

i2c = I2C(board.I2C0_SCL, board.I2C0_SDA)


# ---------------------------------------------------------
# Fake Display
# ---------------------------------------------------------

class Display:
    width = 17
    height = 7

    def __init__(self, i2c=None):
        self.buffer = [[0] * self.width for _ in range(self.height)]

    @staticmethod
    def pixel_addr(x, y):
        return 0

    def clear(self):
        for y in range(self.height):
            for x in range(self.width):
                self.buffer[y][x] = 0

    def scroll(self, value, brightness=30):
        pass

    def show(self, value, brightness=30):
        pass

    def reset(self):
        self.clear()

    def fill(self, color=None, blink=None, frame=None):
        pass

    def pixel(self, x, y, color=None, blink=None, frame=None):
        if 0 <= x < self.width and 0 <= y < self.height:
            self.buffer[y][x] = 1

    def image(self, img, blink=None, frame=None):
        pass


# ---------------------------------------------------------
# Fake LED
# ---------------------------------------------------------

class Led:
    def __init__(self, pin=None):
        self.state = False

    def on(self):
        self.state = True

    def off(self):
        self.state = False

    def toggle(self):
        self.state = not self.state


# ---------------------------------------------------------
# Fake Button
# ---------------------------------------------------------

class Button:
    def __init__(self, pin=None):
        self._pressed = False

    def is_pressed(self):
        return self._pressed

    def was_pressed(self):
        return False


# ---------------------------------------------------------
# Fake Image (placeholder)
# ---------------------------------------------------------

class Image:
    def __new__(cls, value=None):
        return [[0, 0, 0]]

    NO = b""
    SQUARE = b""
    RECTANGLE = b""
    RHOMBUS = b""
    TARGET = b""
    CHESSBOARD = b""
    HAPPY = b""
    SAD = b""
    YES = b""
    HEART = b""
    TRIANGLE = b""
    CHAGRIN = b""
    SMILING_FACE = b""
    CRY = b""
    DOWNCAST = b""
    LOOK_RIGHT = b""
    LOOK_LEFT = b""
    TONGUE = b""
    PEEK_RIGHT = b""
    PEEK_LEFT = b""
    TEAR_EYES = b""
    PROUD = b""
    SNEER_LEFT = b""
    SNEER_RIGHT = b""
    SUPERCILIOUS_LOOK = b""
    EXCITED = b""


# ---------------------------------------------------------
# Fake Music
# ---------------------------------------------------------

class Music:
    def __init__(self, pin=None):
        pass


# ---------------------------------------------------------
# Modulové instance (odpovídají reálnému pico:ed API)
# ---------------------------------------------------------

display = Display(i2c)
button_a = Button()
button_b = Button()
led = Led()
music = Music()
