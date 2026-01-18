"""
pca9633.py – ovladač PWM driveru PCA9633 pro JoyCar robota.

Tento modul poskytuje:
- registry PCA9633,
- třídu PCA9633 pro řízení 4 PWM kanálů motorů.

Použití:
    pca = PCA9633(i2c)
    pca.writeRegister(PCA9633_registers.PWM0, 128)
"""

from joycar.i2c import I2C


class PCA9633_registers:
    """Adresy registrů PCA9633."""
    MODE1 = 0x00
    MODE2 = 0x01
    PWM0 = 0x02
    PWM1 = 0x03
    PWM2 = 0x04
    PWM3 = 0x05
    GRPPWM = 0x06
    GRPFREQ = 0x07
    LEDOUT = 0x08


class PCA9633:
    """
    Ovladač PWM driveru PCA9633.

    Umožňuje:
        - čtení registrů,
        - zápis registrů,
        - řízení 4 PWM kanálů motorů.

    Atributy:
        _i2c (I2C): Bezpečný I2C wrapper.
        _address (int): I2C adresa zařízení.
    """

    def __init__(self, i2c: I2C, address=0x62):
        self._i2c = i2c
        self._address = address

    def readRegister(self, reg: int) -> int:
        """Přečte hodnotu z registru."""
        readbuffer = bytearray(1)
        with self._i2c:
            self._i2c.write_readinto(self._address, bytes([reg]), readbuffer)
        return readbuffer[0]

    def writeRegister(self, reg: int, value: int) -> None:
        """Zapíše hodnotu do registru."""
        with self._i2c:
            self._i2c.write(self._address, bytes([reg, value]))

    def writeTwoRegisters(self, firstReg: int, firstValue: int, secondReg: int, secondValue: int) -> None:
        """Zapíše hodnoty do dvou registrů."""
        with self._i2c:
            self._i2c.write(self._address, bytes([firstReg, firstValue]))
            self._i2c.write(self._address, bytes([secondReg, secondValue]))
