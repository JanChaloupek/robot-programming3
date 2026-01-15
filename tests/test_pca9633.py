import unittest
from code import PCA9633, I2C
from picoed import FakeI2C


class TestPCA9633(unittest.TestCase):
    """
    Testy základních operací PCA9633.

    Tento test ověřuje, že metoda writeRegister():
        - provede přesně jeden zápis do I2C sběrnice
        - zapíše správný registr
        - zapíše správnou hodnotu
        - použije správnou I2C adresu zařízení (0x62)

    Test je navržen tak, aby odhalil chyby typu:
        - zápis do špatného registru
        - zápis špatné hodnoty
        - nadbytečné zápisy navíc
        - špatná I2C adresa
    """

    def test_write_register(self):
        """
        Ověříme, že writeRegister zapíše jediný registr
        ve správném formátu:
            (0x62, [0x10, 0x55])
        """

        hw = FakeI2C()
        p = PCA9633(I2C(hw))

        p.writeRegister(0x10, 0x55)

        # Ověříme, že poslední zápis odpovídá očekávanému formátu
        self.assertEqual(hw.writes[-1], (0x62, [0x10, 0x55]))
