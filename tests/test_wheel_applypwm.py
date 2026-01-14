import unittest
from code import Wheel, DirectionEnum, PCA9633, I2C
from tests.fake_hw import FakeI2C

class TestWheelApplyPwm(unittest.TestCase):
    def test_apply_pwm_without_reverse(self):
        hw = FakeI2C()
        wheel = Wheel(DirectionEnum.LEFT, PCA9633(I2C(hw)))

        wheel.ridePwm(100)
        wheel.update()

        self.assertEqual(hw.writes[-1][1][-1], 100)
