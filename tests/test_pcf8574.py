import unittest
from code import PCF8574, I2C
from tests.fake_hw import FakeI2C

class TestPCF8574(unittest.TestCase):
    def test_read(self):
        hw = FakeI2C()
        hw.reads.append([0xAA])
        p = PCF8574(I2C(hw))
        self.assertEqual(p.read(), 0xAA)
