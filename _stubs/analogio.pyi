# _stubs/analogio.pyi

class AnalogIn:
    """
    Reprezentuje analogový vstup (ADC) v CircuitPythonu.

    Parametry:
        pin – objekt reprezentující pin (např. board.A0)

    Metody:
        read() -> int
            Vrací aktuální hodnotu ADC v rozsahu 0–65535.

        deinit()
            Uvolní ADC kanál.
    """

    def __init__(self, pin): ...
    def deinit(self) -> None: ...
    def read(self) -> int: ...
