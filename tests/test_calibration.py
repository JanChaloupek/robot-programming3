"""
test_calibration.py – Unit testy kalibračních faktorů a podpory motorů PCA9633 a PCA9685.
"""

import unittest
from joycar.calibration import CalibrateFactors
from joycar.wheel import Wheel
from joycar.direction import DirectionEnum
from busio import I2C as FakeI2C
from joycar.i2c import I2C
from joycar.pca9633 import PCA9633
from joycar.pca9685 import PCA9685


class TestCalibration(unittest.TestCase):
    """Testuje výpočet PWM ze zadané úhlové rychlosti a limity pro různé typy budičů."""

    def test_calculate_pwm_linear(self):
        # PWM = a * |omega| + b
        # Pro a=10, b=20 a omega=5 -> 10*5 + 20 = 70
        cal = CalibrateFactors(a=10.0, b=20.0, maxPwm=255)
        self.assertEqual(cal.calculatePwm(5.0), 70)
        self.assertEqual(cal.calculatePwm(-5.0), -70)
        self.assertEqual(cal.calculatePwm(0.0), 0)

    def test_for_pca9633_preset(self):
        cal = CalibrateFactors.forPCA9633(a=17.0, b=28.0)
        self.assertEqual(cal.maxPwm, 255)
        self.assertEqual(cal.minPwm_WhenStopped, 20)
        self.assertEqual(cal.minPwm_InMotion, 15)

        # Omezení horní hranicí 255
        self.assertEqual(cal.calculatePwm(50.0), 255)
        self.assertEqual(cal.calculatePwm(-50.0), -255)

    def test_for_pca9685_preset(self):
        cal = CalibrateFactors.forPCA9685()
        self.assertEqual(cal.maxPwm, 4095)
        self.assertEqual(cal.minPwm_WhenStopped, 320)
        self.assertEqual(cal.minPwm_InMotion, 240)

        # Omezení horní hranicí 4095
        self.assertEqual(cal.calculatePwm(100.0), 4095)
        self.assertEqual(cal.calculatePwm(-100.0), -4095)

    def test_wheel_with_calibration(self):
        hw = FakeI2C()
        driver = PCA9633(I2C(hw))
        cal = CalibrateFactors.forPCA9633(a=15.0, b=30.0)
        wheel = Wheel(DirectionEnum.LEFT, driver, calibration=cal)

        # Nastavení úhlové rychlosti v rad/s
        wheel.setAngularSpeedRad(4.0)
        # 15 * 4 + 30 = 90
        self.assertEqual(wheel._targetPwm, 90)

    def test_wheel_with_pca9685(self):
        hw = FakeI2C()
        driver = PCA9685(I2C(hw))
        cal = CalibrateFactors.forPCA9685(a=200.0, b=400.0)
        wheel = Wheel(DirectionEnum.RIGHT, driver, calibration=cal)

        self.assertEqual(wheel.maxPwm, 4095)
        wheel.setAngularSpeedRad(5.0)
        # 200 * 5 + 400 = 1400
        self.assertEqual(wheel._targetPwm, 1400)


if __name__ == "__main__":
    unittest.main()
