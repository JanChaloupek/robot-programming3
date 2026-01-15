import unittest
from code import Sensors, PCF8574, I2C
from picoed import FakeI2C


class TestSensorsUpdate(unittest.TestCase):
    """
    Testy periodického čtení senzorů.

    Tento test ověřuje, že metoda update():
        - provede nové čtení z PCF8574, pokud perioda vypršela
        - správně aplikuje XOR masku 0x1C pro invertování logiky senzorů
        - uloží výsledek do atributu _data
        - správně pracuje s FakeI2C simulací

    Test slouží jako sanity‑check správné implementace periodického čtení.
    """

    def test_periodic_update(self):
        """
        Ověříme, že update() načte nová data,
        pokud perioda byla uměle nastavena jako vypršela.

        První čtení: 0b00011100 (ignorováno)
        Druhé čtení: 0b00000000 → po XOR s 0x1C = 0b00011100
        """

        hw = FakeI2C()
        hw.reads.append([0b00011100])  # první čtení při konstrukci

        s = Sensors(PCF8574(I2C(hw)))

        # simulace vypršení periody
        s._periodRead._startTime = 0
        s._periodRead.timeout_ms = -1

        hw.reads.append([0b00000000])  # nové čtení při update()

        s.update()

        # očekáváme XOR s maskou 0x1C
        self.assertEqual(s._data, 0b00000000 ^ 0x1C)
