"""
picoed.py – společný stub pro VS Code a fake hardware pro testy.

Tento soubor:
- poskytuje API kompatibilní s reálným pico:ed modulem v CircuitPythonu
- neimportuje žádné hardware knihovny (digitalio, busio, microcontroller)
- funguje jako fake hardware při testech na PC
- poskytuje třídy a atributy pro VS Code (autocomplete, typy)

Reálný pico:ed modul je součástí CircuitPythonu a NEpublikuje se.
Tento soubor slouží pouze pro vývoj a testování na PC.
"""

# ---------------------------------------------------------
# Fake I2C (pro PCA9633 a další I2C zařízení)
# ---------------------------------------------------------

class FakeI2C:
    def __init__(self):
        self.locked = False
        self.writes = []
        self.reads = []

    def try_lock(self):
        if not self.locked:
            self.locked = True
            return True
        return False

    def unlock(self):
        self.locked = False

    def scan(self):
        return [0x38, 0x62]

    def readfrom_into(self, addr, buf, start=0, end=None):
        data = self.reads.pop(0) if self.reads else [0]
        for i in range(len(buf)):
            buf[i] = data[i] if i < len(data) else 0

    def writeto(self, addr, buf):
        self.writes.append((addr, list(buf)))

    def writeto_then_readfrom(self, addr, wbuf, rbuf):
        self.writes.append((addr, list(wbuf)))
        self.readfrom_into(addr, rbuf)


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
# Fake Image (jen placeholder)
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

i2c = FakeI2C()
display = Display(i2c)
button_a = Button()
button_b = Button()
led = Led()
music = Music()
