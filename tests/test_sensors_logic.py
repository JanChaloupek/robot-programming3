import unittest
from joycar.sensors import Sensors
from _stubs.busio import I2C as FakeI2C
from tests.create import createSensors


class TestSensorsLogic(unittest.TestCase):
    """
    Testy logiky čtení a vyhodnocování senzorů čáry.

    Testy ověřují, že:
        - surová hodnota z PCF8574 je správně invertována pomocí XOR masky
        - jednotlivé senzory lze testovat pomocí areActive()
        - skupiny senzorů lze testovat pomocí isAnyActive()
        - FakeI2C správně simuluje hodnoty vrácené z I2C sběrnice

    Tyto testy slouží jako sanity‑check správné interpretace bitových masek.
    """

    def test_are_active(self):
        """
        Ověříme, že areActive() správně detekuje aktivní levý senzor.

        raw = 0b00000100
        po XOR s maskou 0x1C (0b00011100) → levý senzor bude aktivní
        """

        hw = FakeI2C()
        hw.queue_read([0b00000100])  # simulace hodnoty z I2C

        s = createSensors(hw)

        self.assertTrue(s.areActive(Sensors.LineLeft))

    def test_is_any_active(self):
        """
        Ověříme, že isAnyActive() správně detekuje,
        že alespoň jeden senzor ve skupině LineAll je aktivní.

        raw = 0b00010100 → po XOR bude aktivních více senzorů
        """

        hw = FakeI2C()
        hw.queue_read([0b00010100])

        s = createSensors(hw)

        self.assertTrue(s.isAnyActive(Sensors.LineAll))
