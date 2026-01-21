import unittest
from _stubs.busio import I2C as FakeI2C
from tests.create import createSensors

class TestSensors(unittest.TestCase):
    def test_read_and_invert(self):
        hw = FakeI2C()
        hw.queue_read([0b00011100])
        s = createSensors(hw)
        self.assertEqual(s.getSensorData(0x1C), 0)
