"""
pcf8574.py – ovladač I/O expanderu PCF8574 pro JoyCar robota.

Tento modul poskytuje třídu PCF8574, která umožňuje:
- čtení vstupů (senzory),
- zápis výstupů (pokud by byly potřeba),
- bezpečnou komunikaci přes I2C wrapper.

Použití:
    pcf = PCF8574(i2c)
    value = pcf.read()
"""

from joycar.i2c import I2C


class PCF8574:
    """
    Ovladač PCF8574 I/O expanderu.

    Atributy:
        _i2c (I2C): Bezpečný I2C wrapper.
        _address (int): I2C adresa zařízení.
    """

    def __init__(self, i2c: I2C, address: int = 0x38) -> None:
        self._i2c = i2c
        self._address = address

    def write(self, data: int) -> None:
        """Zapíše jeden bajt do expanderu."""
        with self._i2c:
            self._i2c.write(self._address, bytes([data & 0xFF]))

    def read(self) -> int:
        """Přečte jeden bajt z expanderu."""
        with self._i2c:
            return self._i2c.read(self._address, 1)[0]
