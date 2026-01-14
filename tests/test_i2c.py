import unittest
from code import I2C
from tests.fake_hw import FakeI2C

class TestI2C(unittest.TestCase):
    def test_scan(self):
        hw = FakeI2C()
        i2c = I2C(hw)
        self.assertEqual(i2c.scan(), [0x38, 0x62])

    def test_write(self):
        hw = FakeI2C()
        i2c = I2C(hw)
        i2c.write(0x10, b"\x01\x02")
        self.assertEqual(hw.writes[-1], (0x10, [1,2]))
