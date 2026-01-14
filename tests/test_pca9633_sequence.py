import unittest
from code import PCA9633, I2C
from tests.fake_hw import FakeI2C

class TestPCA9633Sequence(unittest.TestCase):
    def test_write_two_registers_sequence(self):
        hw = FakeI2C()
        p = PCA9633(I2C(hw))

        p.writeTwoRegisters(0x02, 10, 0x03, 20)

        self.assertEqual(hw.writes[-2], (0x62, [0x02, 10]))
        self.assertEqual(hw.writes[-1], (0x62, [0x03, 20]))
