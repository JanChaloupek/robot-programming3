"""
Fake implementace CircuitPython knihovny `neopixel`.

Simuluje adresovatelné RGB/RGBW LED pro vývoj a testování na PC.
Chování je deterministické a ukládá barvy do Python seznamu.
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
        - generuje přesné časování signálu
        - používá DMA nebo přesné instrukce

    Ve fake verzi:
        - funkce nedělá nic
        - slouží pouze pro kompatibilitu API
    """
    pass


# ---------------------------------------------------------
# Fake Pixel Buffer
# ---------------------------------------------------------

class _PixelBuf:
    """
    Fake pixel buffer používaný jako test double.

    Vlastnosti:
        _pixels       – seznam barev [(r,g,b), ...]
        write_called  – True, pokud byla volána show()
        brightness    – symbolická hodnota (neaplikuje se)
        auto_write    – pokud True, __setitem__ a fill() volají show()
        byteorder     – pořadí barev (RGB/GRB/RGBW/GRBW)
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

        Ve fake verzi:
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

    Vlastnosti:
        pin     – fake DigitalInOut pin
        _power  – symbolická hodnota (nepoužívá se)

    Chování:
        - ukládá barvy do Python seznamu
        - podporuje context manager
        - auto_write funguje stejně jako v CP
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

        Ve fake verzi:
            - pouze volá neopixel_write() (které nic nedělá)
        """
        neopixel_write(self.pin, buffer)
