import unittest
from code import Wheels, PCA9633, I2C
from tests.fake_hw import FakeI2C

class FakeWheel:
    def __init__(self):
        self.updated = False
    def update(self):
        self.updated = True

class TestWheelsUpdate(unittest.TestCase):
    def test_update_calls_both_wheels(self):
        hw = FakeI2C()
        wheels = Wheels(PCA9633(I2C(hw)))

        wheels._wheels = {
            "left": FakeWheel(),
            "right": FakeWheel()
        }

        wheels.update()

        self.assertTrue(wheels._wheels["left"].updated)
        self.assertTrue(wheels._wheels["right"].updated)
