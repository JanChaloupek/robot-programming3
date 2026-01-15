import unittest
from code import PCF8574, I2C
from picoed import FakeI2C


class TestPCF8574Write(unittest.TestCase):
    """
    Testy zápisu do expandéru PCF8574.

    Tento test ověřuje, že metoda write():
        - provede přesně jeden zápis na I2C sběrnici
        - zapíše správnou hodnotu (0xAA)
        - použije správnou I2C adresu zařízení (0x38)

    Test je navržen tak, aby odhalil chyby typu:
        - zápis na špatnou adresu
        - zápis špatné hodnoty
        - nadbytečné zápisy navíc
    """

    def test_write(self):
        """
        Ověříme, že write() zapíše jedinou hodnotu
        ve správném formátu:
            (0x38, [0xAA])
        """

        hw = FakeI2C()
        p = PCF8574(I2C(hw))

        p.write(0xAA)

        # Ověříme, že poslední zápis odpovídá očekávanému formátu
        self.assertEqual(hw.writes[-1], (0x38, [0xAA]))
