import unittest
from code import Sensors, PCF8574, I2C
from picoed import FakeI2C

class TestSensors(unittest.TestCase):
    def test_read_and_invert(self):
        hw = FakeI2C()
        hw.reads.append([0b00011100])
        s = Sensors(PCF8574(I2C(hw)))
        self.assertEqual(s.getSensorData(0x1C), 0)
