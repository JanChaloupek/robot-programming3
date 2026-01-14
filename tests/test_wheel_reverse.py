import unittest
from code import Wheel, DirectionEnum, PCA9633, I2C
from tests.fake_hw import FakeI2C

class TestWheelReverse(unittest.TestCase):
    def setUp(self):
        self.hw = FakeI2C()
        self.pca = PCA9633(I2C(self.hw))
        self.wheel = Wheel(DirectionEnum.LEFT, self.pca)

    def test_reverse_sequence(self):
        # 1) Rozjeď dopředu
        self.wheel.ridePwm(100)
        self.wheel.update()
        self.assertEqual(self.hw.writes[-1][1][-1], 100)

        # 2) Požaduj reverz
        self.wheel.ridePwm(-100)
        self.wheel.update()

        # První krok reverzu musí být STOP (PWM=0)
        self.assertEqual(self.hw.writes[-1][1][-1], 0)

        # 3) Timer ještě nevypršel → PWM se nesmí změnit
        self.wheel.update()
        self.assertEqual(self.hw.writes[-1][1][-1], 0)

        # 4) Simuluj vypršení timeoutu
        self.wheel._timer._startTime = 0
        self.wheel._timer.timeout_ms = -1  # okamžitý timeout

        self.wheel.update()

        # Teď se musí aplikovat nový PWM
        self.assertEqual(self.hw.writes[-1][1][-1], 100)  # -100 se zapisuje jako 100 (absolutní hodnota)
