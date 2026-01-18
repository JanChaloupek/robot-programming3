import unittest
from lib_vsc_only.busio import I2C as FakeI2C
from tests.create import createSensors

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
        hw.queue_read(bytes([0b00011100]))  # první čtení při konstrukci
        s = createSensors(hw)

        # simulace vypršení periody
        s._periodRead._startTime = 0
        s._periodRead.timeout_ms = -1

        hw.queue_read(bytes([0b00000000]))  # nové čtení při update()

        s.update()

        # očekáváme XOR s maskou 0x1C
        self.assertEqual(s._data, 0b00000000 ^ 0x1C)
