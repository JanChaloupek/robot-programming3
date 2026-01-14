import unittest
from code import Wheel, DirectionEnum, PCA9633, I2C
from tests.fake_hw import FakeI2C

class TestWheel(unittest.TestCase):
    def test_apply_deadzone(self):
        hw = FakeI2C()
        w = Wheel(DirectionEnum.LEFT, PCA9633(I2C(hw)))
        w.ridePwm(5)
        self.assertEqual(w._targetPwm, 20)

    def test_max_limit(self):
        hw = FakeI2C()
        w = Wheel(DirectionEnum.LEFT, PCA9633(I2C(hw)))
        w.ridePwm(999)
        self.assertEqual(w._targetPwm, 255)
