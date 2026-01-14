import unittest
from code import Wheel, DirectionEnum, PCA9633, I2C
from tests.fake_hw import FakeI2C

class TestWheelSanitize(unittest.TestCase):
    def setUp(self):
        self.hw = FakeI2C()
        self.wheel = Wheel(DirectionEnum.LEFT, PCA9633(I2C(self.hw)))

    def test_zero_stays_zero(self):
        self.assertEqual(self.wheel._sanitizePwm(0), 0)

    def test_deadzone_applied(self):
        self.assertEqual(self.wheel._sanitizePwm(5), 20)

    def test_max_limit_applied(self):
        self.assertEqual(self.wheel._sanitizePwm(999), 255)

    def test_negative_deadzone(self):
        self.assertEqual(self.wheel._sanitizePwm(-10), -20)

    def test_negative_max_limit(self):
        self.assertEqual(self.wheel._sanitizePwm(-999), -255)
