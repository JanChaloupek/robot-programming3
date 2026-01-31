"""
Stub rozhraní pro CircuitPython knihovnu `neopixel`.

Obsahuje třídy a konstanty potřebné pro autocomplete a typovou kontrolu.
"""

RGB: str
GRB: str
RGBW: str
GRBW: str

def neopixel_write(pin, buf) -> None: ...

class _PixelBuf:
    """
    Reprezentuje buffer adresovatelných LED.
    """

    def __init__(
        self,
        n: int,
        *,
        brightness: float = 1.0,
        byteorder: str = "GRB",
        auto_write: bool = True
    ): ...

    def __len__(self) -> int: ...
    def __getitem__(self, index: int): ...
    def __setitem__(self, index: int, value) -> None: ...
    def fill(self, color) -> None: ...
    def show(self) -> None: ...

class NeoPixel(_PixelBuf):
    """
    Reprezentuje adresovatelný LED pásek nebo pole LED.
    """

    pin: object

    def __init__(
        self,
        pin,
        n: int,
        *,
        bpp: int = 3,
        brightness: float = 1.0,
        auto_write: bool = True,
        pixel_order: str | None = None
    ): ...

    def deinit(self) -> None: ...
    def __enter__(self): ...
    def __exit__(self, exc_type, exc, tb): ...
    @property
    def n(self) -> int: ...
    def write(self) -> None: ...
    def _transmit(self, buffer) -> None: ...
