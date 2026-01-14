import unittest
from code import Wheels, PCA9633, I2C
from tests.fake_hw import FakeI2C

class TestWheels(unittest.TestCase):
    def test_left_right(self):
        w = Wheels(PCA9633(I2C(FakeI2C())))
        self.assertIsNotNone(w.left)
        self.assertIsNotNone(w.right)
