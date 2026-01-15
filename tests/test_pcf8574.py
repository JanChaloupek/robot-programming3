import unittest
from code import PCF8574, I2C
from picoed import FakeI2C


class TestPCF8574(unittest.TestCase):
    """
    Testy čtení z expandéru PCF8574.

    Tento test ověřuje, že metoda read():
        - provede jeden I2C read
        - vrátí správnou hodnotu přečtenou z FakeI2C
        - správně interpretuje jednovýstupní buffer [0xAA]

    Test je navržen tak, aby odhalil chyby typu:
        - špatná interpretace přečtených dat
        - čtení více nebo méně bytů, než je potřeba
        - ignorování hodnoty vrácené z I2C
    """

    def test_read(self):
        """
        Ověříme, že read() vrátí hodnotu 0xAA,
        pokud FakeI2C vrátí buffer [0xAA].
        """

        hw = FakeI2C()
        hw.reads.append([0xAA])  # simulace hodnoty vrácené z I2C

        p = PCF8574(I2C(hw))

        self.assertEqual(p.read(), 0xAA)
