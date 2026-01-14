import unittest
from code import PCA9633, I2C
from tests.fake_hw import FakeI2C

class TestPCA9633(unittest.TestCase):
    def test_write_register(self):
        hw = FakeI2C()
        p = PCA9633(I2C(hw))
        p.writeRegister(0x10, 0x55)
        self.assertEqual(hw.writes[-1], (0x62, [0x10, 0x55]))
