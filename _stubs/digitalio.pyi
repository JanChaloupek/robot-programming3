# ================================
# _stubs/digitalio.pyi
# ================================

"""
Stub rozhraní pro CircuitPython modul `digitalio`.

Obsahuje třídy Direction, Pull a DigitalInOut s jejich veřejným API.
"""

class Direction:
    INPUT: int
    OUTPUT: int

class Pull:
    UP: int
    DOWN: int

class DigitalInOut:
    """
    Reprezentuje digitální pin (GPIO) v CircuitPythonu.
    """

    pin: object
    direction: int | None
    pull: int | None
    value: bool

    def __init__(self, pin): ...
    def switch_to_output(self, value: bool = False) -> None: ...
    def switch_to_input(self, pull: int | None = None) -> None: ...
    def deinit(self) -> None: ...


