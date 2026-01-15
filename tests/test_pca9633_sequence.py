import unittest
from code import PCA9633, I2C
from picoed import FakeI2C


class TestPCA9633Sequence(unittest.TestCase):
    """
    Testy sekvenčního zápisu do dvou registrů PCA9633.

    Tento test ověřuje, že metoda writeTwoRegisters():
        - provede přesně dva zápisy do I2C sběrnice
        - zapíše správné adresy registrů
        - zapíše správné hodnoty
        - zachová pořadí zápisů (nejprve první registr, poté druhý)

    Test je navržen tak, aby odhalil chyby typu:
        - špatné pořadí zápisů
        - zápis do špatného registru
        - zápis špatné hodnoty
        - nadbytečné zápisy navíc
    """

    def test_write_two_registers_sequence(self):
        """
        Ověříme, že writeTwoRegisters zapíše přesně dva registry
        v přesném pořadí:
            1) (0x02, 10)
            2) (0x03, 20)
        """

        hw = FakeI2C()
        p = PCA9633(I2C(hw))

        p.writeTwoRegisters(0x02, 10, 0x03, 20)

        # Ověříme, že byly provedeny přesně dva zápisy
        self.assertEqual(len(hw.writes), 2)

        # Ověříme obsah zápisů
        self.assertEqual(hw.writes[0], (0x62, [0x02, 10]))
        self.assertEqual(hw.writes[1], (0x62, [0x03, 20]))
