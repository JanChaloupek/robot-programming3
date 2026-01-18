"""
neopixel.py – společný stub pro VS Code a fake hardware pro testy.

Tento modul napodobuje CircuitPython knihovnu `neopixel`, která slouží
k ovládání adresovatelných RGB/RGBW LED (WS2812, SK6812 atd.).

V této verzi:
- modul je určený pro vývoj na PC (VS Code / Pylance)
- funguje jako fake hardware pro unit testy
- nevyžaduje žádný skutečný mikrořadič ani LED pásky
- chová se deterministicky a ukládá barvy do Python seznamu
- podporuje auto_write, brightness a pixel_order (symbolicky)

Reálný modul `neopixel` je součástí CircuitPythonu a není dostupný na PC.
Tento soubor slouží pro výuku, vývoj a testování.
"""

import digitalio

# ---------------------------------------------------------
# Pixel order constants (kompatibilní s CircuitPython API)
# ---------------------------------------------------------

RGB = "RGB"
GRB = "GRB"
RGBW = "RGBW"
GRBW = "GRBW"


def neopixel_write(pin, buf):
    """
    Fake implementace nízkoúrovňového zápisu do NeoPixel LED.

    V reálném CircuitPythonu:
        - neopixel_write generuje přesné časování signálu
        - používá DMA nebo přesné instrukce

    V této fake verzi:
        - funkce nedělá nic
        - slouží pouze pro kompatibilitu API
    """
    pass


# ---------------------------------------------------------
# Fake Pixel Buffer
# ---------------------------------------------------------

class _PixelBuf:
    """
    Fake pixel buffer používaný jako stub i test double.

    V reálném zařízení:
        - PixelBuf spravuje interní buffer LED
        - podporuje různé formáty (RGB, GRB, RGBW)
        - brightness se aplikuje při zápisu

    V této fake verzi:
        - barvy se ukládají do Python seznamu self._pixels
        - brightness se neaplikuje (symbolické)
        - auto_write volá show() automaticky
        - show() pouze nastaví příznak write_called

    Atributy:
        _pixels       – seznam barev [(r,g,b), ...]
        write_called  – True, pokud byla volána show()
    """

    def __init__(self, n, *, brightness=1.0, byteorder="GRB", auto_write=True):
        self._n = n
        self.brightness = brightness
        self.auto_write = auto_write
        self.byteorder = byteorder

        # Fake LED buffer
        self._pixels = [(0, 0, 0)] * n

        # Pro testy: zda byla volána show()
        self.write_called = False

    def __len__(self):
        """Vrací počet LED."""
        return self._n

    def __getitem__(self, index):
        """Vrací barvu LED na daném indexu."""
        return self._pixels[index]

    def __setitem__(self, index, value):
        """
        Nastaví barvu LED.

        Pokud je auto_write=True, automaticky zavolá show().
        """
        self._pixels[index] = tuple(value)
        if self.auto_write:
            self.show()

    def fill(self, color):
        """
        Nastaví stejnou barvu pro všechny LED.

        Pokud je auto_write=True, automaticky zavolá show().
        """
        self._pixels = [tuple(color)] * self._n
        if self.auto_write:
            self.show()

    def show(self):
        """
        Fake implementace zápisu do LED.

        V reálném zařízení:
            - odešle buffer do LED přes přesné časování

        V této fake verzi:
            - pouze nastaví příznak write_called=True
            - testy mohou ověřit, že došlo k zápisu
        """
        self.write_called = True


# ---------------------------------------------------------
# Fake NeoPixel
# ---------------------------------------------------------

class NeoPixel(_PixelBuf):
    """
    Fake implementace třídy NeoPixel z CircuitPythonu.

    V reálném zařízení:
        - NeoPixel ovládá LED přes digitální pin
        - používá PixelBuf pro správu barev
        - podporuje context manager (__enter__/__exit__)

    V této fake verzi:
        - používá DigitalInOut jako fake pin
        - ukládá barvy do Python seznamu
        - je plně testovatelný bez hardware
    """

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
        """
        Inicializuje fake NeoPixel.

        Parametry:
            pin         – libovolný objekt reprezentující pin (např. board.P0)
            n           – počet LED
            bpp         – bytes per pixel (3 = RGB, 4 = RGBW)
            brightness  – symbolická hodnota (neaplikuje se)
            auto_write  – pokud True, změny se ihned projeví
            pixel_order – pořadí barev (RGB/GRB/RGBW/GRBW)
        """
        if pixel_order is None:
            pixel_order = GRB if bpp == 3 else GRBW

        super().__init__(
            n,
            brightness=brightness,
            byteorder=pixel_order,
            auto_write=auto_write,
        )

        # Fake pin object
        self.pin = digitalio.DigitalInOut(pin)
        self.pin.direction = digitalio.Direction.OUTPUT
        self._power = None

    def deinit(self):
        """
        Fake uvolnění NeoPixel objektu.

        V reálném zařízení:
            - vypne LED
            - uvolní pin

        Zde:
            - nastaví všechny LED na (0,0,0)
            - označí zápis
            - zneplatní pin
        """
        self.fill((0, 0, 0))
        self.show()
        self.pin = None
        self._power = None

    def __enter__(self):
        """Podpora context manageru."""
        return self

    def __exit__(self, exc_type, exc, tb):
        """Při ukončení context manageru vypne LED."""
        self.deinit()

    @property
    def n(self):
        """Vrací počet LED (kompatibilní s CircuitPython API)."""
        return len(self)

    def write(self):
        """
        Alias pro show().

        CircuitPython používá write() jako starší API.
        """
        self.show()

    def _transmit(self, buffer):
        """
        Fake nízkoúrovňový přenos dat.

        V reálném zařízení:
            - odesílá raw buffer do LED

        Zde:
            - pouze volá neopixel_write() (které nic nedělá)
        """
        neopixel_write(self.pin, buffer)
