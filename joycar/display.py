"""
display.py – rozšířený ovladač displeje pro JoyCar robota.

Tento modul obsahuje:

- třídu Battery pro měření napájecího napětí,
- třídu Display pro vykreslování na 17×7 LED displej pico:ed,
- podporu ikon, čísel, piktogramů a postupného překreslování,
- kompatibilitu s reálným i fake hardwarem (lib_vsc_only/picoed).

POZOR:
    Aby se změny na displeji skutečně zobrazovaly, je nutné pravidelně
    volat metodu Display.updatePixels() nebo Display.redraw().
    Typicky se volá v hlavní smyčce robota:

        while True:
            robot.update()
            Display.updatePixels()

Display používá interní buffer (__pixelsMap) a mapu změn (__redrawNeeded), 
aby minimalizoval počet zápisů na displej a umožnil postupné vykreslování.

Vykreslování se snaží být neblokující (maximálně 2 pixely v jednom kroku).
"""

from analogio import AnalogIn
from picoed import display as pico_display
from board import P2


# ---------------------------------------------------------
# Battery – měření napájecího napětí
# ---------------------------------------------------------

class Battery:
    pin = AnalogIn(P2)

    # Magická konstanta pro rychlý výpočet napětí baterie.
    #
    # Vysvětlení:
    #   raw = AnalogIn(P2).value vrací hodnotu 0–65535 (16bit)
    #
    #   U_adc = (raw / 65535) * 3.3
    #   U_bat = U_adc * ((10k + 5.6k) / 5.6k)
    #
    #   => U_bat = raw * (3.3 / 65535) * (15.6 / 5.6)
    #   => U_bat = raw * 0.000147
    #
    # Výsledek 0.000147 je zaokrouhlený pro rychlý výpočet,
    # přesnost je pro měření baterie naprosto dostatečná.
    _MAGIC = 0.000147

    @staticmethod
    def getSupplyVoltage() -> float:
        """Vrátí velikost napájecího napětí v jednotkách [Volt]."""
        return Battery.pin.value * Battery._MAGIC

# ---------------------------------------------------------
# Display – hlavní třída pro vykreslování
# ---------------------------------------------------------

class Display:
    """
    Ovladač 17×7 LED displeje pico:ed s podporou:

    - vykreslování jednotlivých pixelů,
    - postupného překreslování (updatePixels),
    - ikon (A, B, C),
    - piktogramů (šipky, čísla, znaky),
    - zobrazení napětí,
    - zobrazení pozice a senzorů.

    Display používá interní buffer a mapu změn, aby minimalizoval počet
    zápisů na displej a umožnil plynulé vykreslování.
    
    DŮLEŽITÉ:
        Displej se nepřekresluje automaticky.
        Je nutné pravidelně volat Display.updatePixels()
        (nebo Display.redraw(), která je blokující).

    Doporučené použití:
        while True:
            robot.update()
            Display.updatePixels()
    """

    rowsDisp = 7
    colsDisp = 17

    # interní buffery
    _pixelsMap = None
    _redrawNeeded = None

    # pozice pro postupné překreslování
    _curCol = 0
    _curRow = 0

    # ---------------------------------------------------------
    # Inicializace
    # ---------------------------------------------------------

    @classmethod
    def _initialize(cls) -> None:
        """Inicializuje interní buffery displeje."""
        cls._pixelsMap = [bytearray(cls.colsDisp) for _ in range(cls.rowsDisp)]
        cls._redrawNeeded = [
            [True for _ in range(cls.colsDisp)]
            for _ in range(cls.rowsDisp)
        ]

    # ---------------------------------------------------------
    # Základní operace
    # ---------------------------------------------------------

    @staticmethod
    def clear() -> None:
        """Vymaže displej i interní buffer."""
        pico_display.fill(0)
        for row in Display._pixelsMap:
            for col in range(len(row)):
                row[col] = 0

    @staticmethod
    def pixel(col: int, row: int, color: int) -> None:
        """
        Nastaví pixel na dané pozici.

        Args:
            col (int): Sloupec (0–16)
            row (int): Řádek (0–6)
            color (int): Barva (0–9)
        """
        if 0 <= col < Display.colsDisp and 0 <= row < Display.rowsDisp:
            old = Display._pixelsMap[row][col]
            Display._pixelsMap[row][col] = color
            Display._redrawNeeded[row][col] |= (old != color)

    # ---------------------------------------------------------
    # Postupné překreslování
    # ---------------------------------------------------------

    @staticmethod
    def redraw() -> None:
        """
        Překreslí celý displej (blokující - 119 kroků).

        POZOR:
            Tato metoda je blokující a trvá ~119 kroků.
            Pro běžný provoz robota používejte raději updatePixels(),
            která překresluje displej postupně a neblokuje hlavní smyčku.
        """
        for _ in range(119):
            Display._updatePixel()

    @staticmethod
    def updatePixels() -> bool:
        """
        Provede dva kroky překreslování.

        Returns:
            bool: True pokud byl překreslen alespoň jeden pixel.
        """
        r1 = Display._updatePixel()
        r2 = Display._updatePixel()
        return r1 or r2

    @staticmethod
    def _updatePixel() -> bool:
        """Provede až 20 pokusů o překreslení jednoho pixelu."""
        for _ in range(20):
            if Display._updatePixelCondition():
                return True
        return False

    @staticmethod
    def _updatePixelCondition() -> bool:
        """Překreslí jeden pixel pokud je potřeba."""
        col = Display._curCol
        row = Display._curRow

        # posun pozice
        Display._curCol += 1
        if Display._curCol >= Display.colsDisp:
            Display._curCol = 0
            Display._curRow += 1
            if Display._curRow >= Display.rowsDisp:
                Display._curRow = 0

        # překreslení
        if Display._redrawNeeded[row][col]:
            Display._redrawNeeded[row][col] = False
            pico_display.pixel(col, row, Display._pixelsMap[row][col])
            return True

        return False

    # ---------------------------------------------------------
    # Piktogramy a ikony
    # ---------------------------------------------------------

    _PICTOGRAMS = {
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

    @staticmethod
    def _bitmap(x: int, y: int, width: int, lines: list[int]) -> None:
        """Vykreslí bitmapu na displej."""
        for iy, line in enumerate(lines):
            for ix in range(width):
                pixel = line & (1 << ix)
                Display.pixel(x + ix, y + iy, 3 if pixel else 0)

    @staticmethod
    def _decimalPoint(show: bool, x: int, y: int = 0, color: int = 9) -> None:
        """Vykreslí nebo smaže desetinnou tečku."""
        Display.pixel(x, y, color if show else 0)

    @staticmethod
    def _iconA(icon: str) -> None:
        Display._bitmap(12, 0, 5, Display._PICTOGRAMS[icon])

    @staticmethod
    def decimalPointAfterA(show: bool) -> None:
        Display._decimalPoint(show, 11)

    @staticmethod
    def _iconB(icon: str) -> None:
        Display._bitmap(6, 0, 5, Display._PICTOGRAMS[icon])

    @staticmethod
    def decimalPointAfterB(show: bool) -> None:
        Display._decimalPoint(show, 5)

    @staticmethod
    def _iconC(icon: str) -> None:
        Display._bitmap(0, 0, 5, Display._PICTOGRAMS[icon])

    # ---------------------------------------------------------
    # Vyšší funkce
    # ---------------------------------------------------------

    @staticmethod
    def supplyVoltage() -> None:
        """Zobrazí napájecí napětí na displeji."""
        voltage = Battery.getSupplyVoltage()
        text = "{:1.1f} V".format(voltage)
        print("Napájecí napětí:", text)

        Display._iconA(text[0])
        Display.decimalPointAfterA(True)
        Display._iconB(text[2])
        Display._iconC(text[4])

    @staticmethod
    def number(num: int) -> None:
        """Zobrazí tříciferné číslo pomocí ikon A, B, C."""
        s = "{:3d}".format(num)
        Display._iconA(s[0])
        Display._iconB(s[1])
        Display._iconC(s[2])

    @staticmethod
    def drive_mode(mode: str) -> None:
        """Zobrazí režim řízení (např. šipku)."""
        Display._iconB(mode)

    @staticmethod
    def position(x: int, y: int) -> None:
        """Zobrazí pozici robota (x,y)."""
        Display._iconA(str(min(9, int(x))))
        Display._iconC(str(min(9, int(y))))

    @staticmethod
    def positionEmpty() -> None:
        """Vymaže pozici."""
        Display._iconA(" ")
        Display._iconC(" ")

    @staticmethod
    def senzors(obstacleLeft: bool, farLeft: bool, left: bool,
                midleLeft: bool, midle35: bool, midleRight: bool,
                right: bool, farRight: bool, obstacleRight: bool,
                bh: int, bl: int) -> None:
        """Zobrazí stav senzorů na spodním řádku displeje."""
        Display.pixel(16, 6, bh if obstacleLeft else bl)
        if farLeft is not None:
            Display.pixel(13, 6, bh if farLeft else bl)
        Display.pixel(11, 6, bh if left else bl)
        if farRight is not None:
            Display.pixel(3, 6, bh if farRight else bl)
        if midleLeft is not None:
            Display.pixel(9, 6, bh if midleLeft else bl)
        if midle35 is not None:
            Display.pixel(8, 6, bh if midle35 else bl)
        Display.pixel(5, 6, bh if right else bl)
        if midleRight is not None:
            Display.pixel(7, 6, bh if midleRight else bl)
        Display.pixel(0, 6, bh if obstacleRight else bl)


# Inicializace bufferů
Display._initialize()
