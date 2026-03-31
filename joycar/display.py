from time import sleep
from picoed import internal_i2c
from board import I2C0_SCL, I2C0_SDA
from busio import I2C

__all__ = ["display", "Display"]

_ADDR = 0x74  # adresa IS31FL3731

internal_i2c.deinit()
fast_i2c = I2C(I2C0_SCL, I2C0_SDA, frequency=650_000)

class Display:

    _needFlush = False
    _instance = None

    rows = 7
    cols = 17

    default_brightness = 32

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._init()
        return cls._instance

    def _init(self, i2c: I2C=fast_i2c):
        self._i2c: I2C = i2c

        # persistentní flush buffer: 1 bajt adresa + 144 bajtů PWM
        self._flushbuf = bytearray(145)
        self._flushbuf[0] = 0x24  # startovní registr PWM

        # inicializace čipu
        while not self._i2c.try_lock():
            pass

        try:
            self._i2c.writeto(_ADDR, b"\xFD\x0B")  # config banka
            self._i2c.writeto(_ADDR, b"\x00\x01")  # wake
            self._i2c.writeto(_ADDR, b"\x01\x00")  # picture mode, frame 0
            self._i2c.writeto(_ADDR, b"\xFD\x00")  # frame 0
            sleep(0.002)

            # povolit všech 144 LED
            for reg in range(0x00, 0x12):
                self._i2c.writeto(_ADDR, bytes([reg, 0xFF]))
        finally:
            self._i2c.unlock()

        self.fill(0)
        self._load_pictograms()
        self._precompute_icon_framebuffer_indices()

    def _load_pictograms(self):
        self._PICTOGRAMS = {
            '>':  [0b00100, 0b00010, 0b11111, 0b00010, 0b00100],  # zatočení doprava
            '<':  [0b00100, 0b01000, 0b11111, 0b01000, 0b00100],  # zatočení doleva
            '^':  [0b00100, 0b00100, 0b10101, 0b01110, 0b00100],  # jedeme rovně
            'v':  [0b00100, 0b01110, 0b10101, 0b00100, 0b00100],  # jedeme zpátky
            'TL': [0b00100, 0b00100, 0b11100, 0b00000, 0b00000],  # rohová křižovatka doleva (turn to left)
            'TR': [0b00100, 0b00100, 0b00111, 0b00000, 0b00000],  # rohová křižovatka doprava (turn to right)
            'IT': [0b00100, 0b00100, 0b11111, 0b00000, 0b00000],  # intersection left-right (T)
            'IL': [0b00100, 0b00100, 0b11100, 0b00100, 0b00100],  # intersection left-straight (T to left)
            'IR': [0b00100, 0b00100, 0b00111, 0b00100, 0b00100],  # intersection right-straight (T to right)
            'I+': [0b00100, 0b00100, 0b11111, 0b00100, 0b00100],  # intersection all directions (+)
            '--': [0b00000, 0b00000, 0b11111, 0b00000, 0b00000],
            ' -': [0b00000, 0b00000, 0b00111, 0b00000, 0b00000],
            '- ': [0b00000, 0b00000, 0b11100, 0b00000, 0b00000],
            '_':  [0b11111, 0b00000, 0b00000, 0b00000, 0b00000],
            '.':  [0b00100, 0b00000, 0b00000, 0b00000, 0b00000],
            '|':  [0b00100, 0b00100, 0b00100, 0b00100, 0b00100],
            '/':  [0b10000, 0b01000, 0b00100, 0b00010, 0b00001],
            '\\': [0b00001, 0b00010, 0b00100, 0b01000, 0b10000],
            's':  [0b11100, 0b00010, 0b01110, 0b01000, 0b00111],
            'x':  [0b10001, 0b01010, 0b00100, 0b01010, 0b10001],
            ' ':  [0b00000, 0b00000, 0b00000, 0b00000, 0b00000],
            ',':  [0b00100, 0b00010, 0b00000, 0b00000, 0b00000],
            '0':  [0b01110, 0b01010, 0b01010, 0b01010, 0b01110],
            '1':  [0b00100, 0b00100, 0b00100, 0b01100, 0b00100],
            '2':  [0b01110, 0b01000, 0b01110, 0b00010, 0b01110],
            '3':  [0b01110, 0b00010, 0b00110, 0b00010, 0b01110],
            '4':  [0b00010, 0b00010, 0b01110, 0b01010, 0b01010],
            '5':  [0b01110, 0b00010, 0b01110, 0b01000, 0b01110],
            '6':  [0b01110, 0b01010, 0b01110, 0b01000, 0b01110],
            '7':  [0b00010, 0b00010, 0b00010, 0b00010, 0b01110],
            '8':  [0b01110, 0b01010, 0b01110, 0b01010, 0b01110],
            '9':  [0b01110, 0b00010, 0b01110, 0b01010, 0b01110],

            'A':  [0b01010, 0b01010, 0b01110, 0b01010, 0b00100],
            'B':  [0b01100, 0b01010, 0b01100, 0b01010, 0b01100],
            'C':  [0b00110, 0b01000, 0b01000, 0b01000, 0b00110],
            'D':  [0b01100, 0b01010, 0b01010, 0b01010, 0b01100],
            'E':  [0b01110, 0b01000, 0b01100, 0b01000, 0b01110],
            'F':  [0b01000, 0b01000, 0b01100, 0b01000, 0b01110],
            'H':  [0b01010, 0b01010, 0b01110, 0b01010, 0b01010],
            'I':  [0b01110, 0b00100, 0b00100, 0b00100, 0b01110],
            'J':  [0b00100, 0b01010, 0b00010, 0b00010, 0b00010],
            'V':  [0b00100, 0b01010, 0b01010, 0b01010, 0b01010],
            'Y':  [0b00100, 0b00100, 0b00100, 0b01010, 0b01010],
            'Z':  [0b01110, 0b01000, 0b00100, 0b00010, 0b01110],
        }

    # ---------------------------------------------------------
    # Předpočítání indexů pro ultra-fast ikony
    # ---------------------------------------------------------
    def _precompute_icon_framebuffer_indices(self):
        self._ICON_FB_A_ON = {}
        self._ICON_FB_B_ON = {}
        self._ICON_FB_C_ON = {}

        self._ICON_FB_A_OFF = {}
        self._ICON_FB_B_OFF = {}
        self._ICON_FB_C_OFF = {}

        positions = {"A": 12, "B": 6, "C": 0}

        for name, lines in self._PICTOGRAMS.items():
            on_pixels = []
            off_pixels = []

            for iy, line in enumerate(lines):
                for ix in range(5):
                    if line & (1 << ix):
                        on_pixels.append((ix, iy))
                    else:
                        off_pixels.append((ix, iy))

            for label, x0 in positions.items():
                on_idx = []
                off_idx = []

                for ix, iy in on_pixels:
                    fb = self._pixelIndex(x0 + ix, iy)
                    on_idx.append(fb)

                for ix, iy in off_pixels:
                    fb = self._pixelIndex(x0 + ix, iy)
                    off_idx.append(fb)

                if label == "A":
                    self._ICON_FB_A_ON [name] = on_idx
                    self._ICON_FB_A_OFF[name] = off_idx
                elif label == "B":
                    self._ICON_FB_B_ON [name] = on_idx
                    self._ICON_FB_B_OFF[name] = off_idx
                else:
                    self._ICON_FB_C_ON [name] = on_idx
                    self._ICON_FB_C_OFF[name] = off_idx

    def set_brightness(self, brightness):
        self.default_brightness = max(0, min(255, brightness))
        
    # ---------------------------------------------------------
    # Pomocné funkce
    # ---------------------------------------------------------
    def _pixelIndex(self, x, y):
        if x > 8:
            x = 17 - x
            y += 8
        else:
            y = 7 - y
        return x * 16 + y

    # ---------------------------------------------------------
    # Základní operace
    # ---------------------------------------------------------
    def pixel(self, x, y, color=None):
        if color is None:
            color = self.default_brightness

        if 0 <= x < self.cols and 0 <= y < self.rows:
            value = max(0, min(255, color))
            idx = self._pixelIndex(x, y)
            self._flushbuf[1 + idx] = value
            self._needFlush = True

    def fill(self, color=None):
        if color is None:
            color = self.default_brightness
        value = max(0, min(255, color))

        for i in range(144):
            self._flushbuf[1 + i] = value
        self._needFlush = True
        
        self.flush()

    def clear(self):
        for i in range(144):
            self._flushbuf[1 + i] = 0
        self._needFlush = True
        self.flush()

    def _bitmap(self, x0, y0, size, bitmap, color=None):
        if color is None:
            color = self.default_brightness

        for iy in range(size):
            line = bitmap[iy]
            for ix in range(size):
                if line & (1 << ix):
                    self.pixel(x0 + ix, y0 + iy, color)
                else:
                    self.pixel(x0 + ix, y0 + iy, 0)

    # ---------------------------------------------------------
    # Ultra-fast bitmapa
    # ---------------------------------------------------------
    def _bitmap_ultra_fast(self, icon, pos, color=None):
        if color is None:
            color = self.default_brightness

        if pos == "A":
            on_list  = self._ICON_FB_A_ON [icon]
            off_list = self._ICON_FB_A_OFF[icon]
        elif pos == "B":
            on_list  = self._ICON_FB_B_ON [icon]
            off_list = self._ICON_FB_B_OFF[icon]
        else:
            on_list  = self._ICON_FB_C_ON [icon]
            off_list = self._ICON_FB_C_OFF[icon]

        fb = self._flushbuf

        for idx in off_list:
            fb[1 + idx] = 0

        for idx in on_list:
            fb[1 + idx] = color

        self._needFlush = True

    # ---------------------------------------------------------
    # Ikony A/B/C
    # ---------------------------------------------------------
    def iconA(self, icon, flush=True, color=None):
        self._bitmap_ultra_fast(icon, "A", color)
        if flush:
            self.flush()

    def iconB(self, icon, flush=True, color=None):
        self._bitmap_ultra_fast(icon, "B", color)
        if flush:
            self.flush()

    def iconC(self, icon, flush=True, color=None):
        self._bitmap_ultra_fast(icon, "C", color)
        if flush:
            self.flush()

    def flush(self):
        if not self._needFlush:
            return
        while not self._i2c.try_lock():
            pass
        try:
            self._i2c.writeto(_ADDR, self._flushbuf)
        finally:
            self._i2c.unlock()
            self._needFlush = False

    def redraw(self):
        self.flush()

    def sensors(self, 
                obstacleLeft, farLeft, left,
                midleLeft, midle35, midleRight,
                right, farRight, obstacleRight,
                bh, bl):

        self.pixel(16, 6, bh if obstacleLeft else bl)
        if farLeft is not None:
            self.pixel(13, 6, bh if farLeft else bl)
        self.pixel(11, 6, bh if left else bl)
        if midleLeft is not None:
            self.pixel(9, 6, bh if midleLeft else bl)
        if midle35 is not None:
            self.pixel(8, 6, bh if midle35 else bl)
        if midleRight is not None:
            self.pixel(7, 6, bh if midleRight else bl)
        self.pixel(5, 6, bh if right else bl)
        if farRight is not None:
            self.pixel(3, 6, bh if farRight else bl)
        self.pixel(0, 6, bh if obstacleRight else bl)
        self.flush()

    def number(self, num,  flush=True) -> None:
        number = "{:3d}".format(num)
        self.iconA(number[0], flush=False)
        self.iconB(number[1], flush=False)
        self.iconC(number[2], flush=False)
        if flush:
            self.flush()

    def drive_mode(self, mode, flush=True, color=None) -> None:
        self.iconB(mode, flush=flush, color=color)

    def _position_base(self, a: str, c: str, flush=True) -> None:
        self.iconA(a, flush=False)
        self.iconC(c, flush=False)
        if flush:
            self.flush()

    def position(self, x: int, y: int, flush=True) -> None:
        self._position_base(str(min(9, int(x))), str(min(9, int(y))), flush=flush)

    def positionEmpty(self, flush=True) -> None:
        self._position_base(" ", " ", flush=flush)


# ---------------------------------------------------------
# Globální instance
# ---------------------------------------------------------
display = Display()
