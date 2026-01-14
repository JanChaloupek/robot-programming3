import unittest
from code import Sensors, PCF8574, I2C
from tests.fake_hw import FakeI2C

class TestSensorsLogic(unittest.TestCase):
    def test_are_active(self):
        hw = FakeI2C()

        # raw = 0b00000100 → po XOR s 0x1C bude levý senzor aktivní
        hw.reads.append([0b00000100])

        s = Sensors(PCF8574(I2C(hw)))

        self.assertTrue(s.areActive(Sensors.LineLeft))

    def test_is_any_active(self):
        hw = FakeI2C()
        hw.reads.append([0b00010100])
        s = Sensors(PCF8574(I2C(hw)))
        self.assertTrue(s.isAnyActive(Sensors.LineAll))
