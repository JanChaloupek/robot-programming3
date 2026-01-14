import unittest
from code import PCF8574, I2C
from tests.fake_hw import FakeI2C

class TestPCF8574Write(unittest.TestCase):
    def test_write(self):
        hw = FakeI2C()
        p = PCF8574(I2C(hw))
        p.write(0xAA)
        self.assertEqual(hw.writes[-1], (0x38, [0xAA]))
