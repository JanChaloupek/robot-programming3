import unittest
from code import Sensors, PCF8574, I2C
from tests.fake_hw import FakeI2C

class TestSensorsUpdate(unittest.TestCase):
    def test_periodic_update(self):
        hw = FakeI2C()
        hw.reads.append([0b00011100])
        s = Sensors(PCF8574(I2C(hw)))

        # simulate time passing
        s._periodRead._startTime = 0
        s._periodRead.timeout_ms = -1

        hw.reads.append([0b00000000])
        s.update()

        self.assertEqual(s._data, 0b00000000 ^ 0x1C)
