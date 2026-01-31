from time import sleep
from picoed import internal_i2c 
from analogio import AnalogIn
from board import P2, I2C0_SCL, I2C0_SDA
from busio import I2C

__all__ = ["display", "battery", "Display", "Battery"]


_ADDR = 0x74  # adresa IS31FL3731

internal_i2c.deinit()
fast_i2c = I2C(
    I2C0_SCL,
    I2C0_SDA,
    frequency=400_000
#    frequency=1_000_000
)

class Display:
    """Singleton ovladač 17×7 displeje pico:ed."""

    _instance = None


    rows = 7
    cols = 17

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._init()
        return cls._instance

    # ---------------------------------------------------------
    # Inicializace
    # ---------------------------------------------------------
    def _init(self, i2c=fast_i2c):
        self._i2c = i2c
        self._pixels = [bytearray(self.cols) for _ in range(self.rows)]
        self._cur_x = 0
        self._cur_y = 0
        self._framebuffer = bytearray(144)

        # --- JEDNORÁZOVÁ INICIALIZACE IS31FL3731 ---
        while not self._i2c.try_lock():
            pass

        try:
            # přepnout do config banky
            self._i2c.writeto(_ADDR, bytes([0xFD, 0x0B]))

            # vypnout shutdown (reg 0x00 = 0x01)
            self._i2c.writeto(_ADDR, bytes([0x00, 0x01]))

            # picture mode (reg 0x01 = 0x00)
            self._i2c.writeto(_ADDR, bytes([0x01, 0x00]))

            # zpět do frame banky 0
            self._i2c.writeto(_ADDR, bytes([0xFD, 0x00]))

            # >>> TADY PŘIDAT PAUZU <<< 
            sleep(0.002)

            # povolit všech 144 LED
            for reg in range(0x00, 0x12):
                self._i2c.writeto(_ADDR, bytes([reg, 0xFF]))

        finally:
            self._i2c.unlock()

        
        # volitelně: vyčistit displej
        self.fill(0)

        # piktogramy 5×5
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
            # 'G':  [0b00110, 0b01010, 0b01000, 0b01000, 0b00110],
            'H':  [0b01010, 0b01010, 0b01110, 0b01010, 0b01010],
            'I':  [0b01110, 0b00100, 0b00100, 0b00100, 0b01110],
            'J':  [0b00100, 0b01010, 0b00010, 0b00010, 0b00010],
            # 'K':  [0b01010, 0b01100, 0b01000, 0b01100, 0b01010],
            # 'L':  [0b01110, 0b01000, 0b01000, 0b01000, 0b01000],
            # 'M':  [0b01010, 0b01010, 0b01110, 0b01110, 0b01010],
            # 'N':  [0b01010, 0b01110, 0b01110, 0b01010, 0b01010],
            # 'O':  [0b00100, 0b01010, 0b01010, 0b01010, 0b00100],
            # 'P':  [0b01000, 0b01000, 0b01100, 0b01010, 0b01100],
            # 'Q':  [0b00110, 0b01110, 0b01010, 0b01010, 0b00100],
            # 'R':  [0b01010, 0b01100, 0b01100, 0b01010, 0b01100],
            # 'S':  [0b01100, 0b00010, 0b00100, 0b01000, 0b00110],
            # 'T':  [0b00100, 0b00100, 0b00100, 0b00100, 0b11111],
            # 'U':  [0b00100, 0b01010, 0b01010, 0b01010, 0b01010],
            'V':  [0b00100, 0b01010, 0b01010, 0b01010, 0b01010],
            # 'W':  [0b01010, 0b01110, 0b01010, 0b01010, 0b01010],
            # 'X':  [0b01010, 0b01010, 0b00100, 0b01010, 0b01010],
            'Y':  [0b00100, 0b00100, 0b00100, 0b01010, 0b01010],
            'Z':  [0b01110, 0b01000, 0b00100, 0b00010, 0b01110],
        }

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
    def _safe_write(self, addr, data, retries=5):
        for attempt in range(retries):
            try:
                self._i2c.writeto(addr, data)
                return True
            except Exception:
                # krátká pauza, aby se I2C i čip vzpamatoval
                sleep(0.0002)  # 200 µs
        return False

    def clear(self):
        for r in range(self.rows):
            for c in range(self.cols):
                self._pixels[r][c] = 0
        self.fill(0)

    def pixel(self, x, y, value):
        if 0 <= x < self.cols and 0 <= y < self.rows:
            self._pixels[y][x] = value

            idx = self._pixelIndex(x, y)
            self._framebuffer[idx] = value

    def fill(self, value):
        while not self._i2c.try_lock():
            pass

        try:
            self._safe_write(_ADDR, bytes([0xFD, 0x00]))

            pwm = bytes([value] * 144)
            # předpokládáme, že jsme už v bank 0 a frame 0 je aktivní
            self._safe_write(_ADDR, bytes([0x24]) + pwm)
        finally:
            self._i2c.unlock()

        # aktualizace interního bufferu
        for r in range(self.rows):
            for c in range(self.cols):
                self._pixels[r][c] = value

        # aktualizace framebufferu
        for i in range(144):
            self._framebuffer[i] = value

    def flush(self):
        while not self._i2c.try_lock():
            pass

        try:
            # 1) Config banka – přepnout aktivní frame na 0
            self._safe_write(_ADDR, bytes([0xFD, 0x0B]))
            self._safe_write(_ADDR, bytes([0x01, 0x00]))  # display frame 0 v picture mode

            # 2) Zpět do frame banky 0
            self._safe_write(_ADDR, bytes([0xFD, 0x00]))

            # 3) Přepsat PWM ve frame 0
            self._safe_write(_ADDR, bytes([0x24]) + self._framebuffer)

        finally:
            self._i2c.unlock()

    # ---------------------------------------------------------
    # Bitmapy a ikony (objektová verze)
    # ---------------------------------------------------------
    def bitmap(self, x, y, width, lines, color=3):
        """Vykreslí bitmapu 5×5 do interního bufferu."""
        for iy, line in enumerate(lines):
            for ix in range(width):
                if line & (1 << ix):
                    self.pixel(x + ix, y + iy, color)
                else:
                    self.pixel(x + ix, y + iy, 0)

    def iconA(self, icon, flush=True):
        self.bitmap(12, 0, 5, self._PICTOGRAMS[icon])
        if flush:
            self.flush()

    def iconB(self, icon, flush=True):  
        self.bitmap(6, 0, 5, self._PICTOGRAMS[icon])
        if flush:
            self.flush()
    
    def iconC(self, icon, flush=True):
        self.bitmap(0, 0, 5, self._PICTOGRAMS[icon])
        if flush:
            self.flush()

    # ---------------------------------------------------------
    # Postupné překreslování
    # ---------------------------------------------------------
    def redraw(self):
        """Překreslí celý displej – rychle a bez blikání."""
        self.flush()

    def updatePixels(self):
        """Překreslí celý displej – rychle a bez blikání."""
        self.flush()

    # ---------------------------------------------------------
    # Senzory – kompatibilita s JoyCar API
    # ---------------------------------------------------------
    def sensors(self, 
                obstacleLeft: bool, farLeft: bool, left: bool,
                midleLeft: bool, midle35: bool, midleRight: bool,
                right: bool, farRight: bool, obstacleRight: bool,
                bh: int, bl: int) -> None:
        """
        Zobrazí stav senzorů na spodním řádku displeje (řádek 6).
        Kompatibilní s původním picoed API.
        """
        # Pozice pixelů převzaté z původní knihovny
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

# ---------------------------------------------------------
# Battery – singleton stejně jako Display
# ---------------------------------------------------------

class Battery:
    _pin = AnalogIn(P2)
    _MAGIC = 0.000147

    @staticmethod
    def voltage():
        return Battery._pin.value * Battery._MAGIC


# ---------------------------------------------------------
# Globální instance
# ---------------------------------------------------------

display = Display()
battery = Battery()
