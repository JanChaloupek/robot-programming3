import unittest
from code import Wheels, PCA9633, I2C
from tests.fake_hw import FakeI2C

class TestWheelsRidePwm(unittest.TestCase):
    def test_ride_pwm_assigns_correctly(self):
        hw = FakeI2C()
        wheels = Wheels(PCA9633(I2C(hw)))

        wheels.ridePwm([100, -50])

        # první update = reverzní STOP
        wheels.update()

        # simulace vypršení reverzního timeoutu
        for wheel in wheels._wheels.values():
            wheel._timer._startTime = 0
            wheel._timer.timeout_ms = -1

        # druhý update = skutečný PWM
        wheels.update()

        # vezmeme všechny nenulové PWM hodnoty
        pwm_values = sorted(
            w[1][1] for w in hw.writes if w[1][1] != 0
        )

        # musí obsahovat PWM pro obě kola
        self.assertIn(100, pwm_values)  # levé kolo
        self.assertIn(50, pwm_values)   # pravé kolo
