"""
Test přímé aplikace PWM na jedno kolo (Wheel) bez reverzní sekvence.

Tento test ukazuje studentům základní chování:
pokud se nemění směr (např. 0 → +100), Wheel musí okamžitě
zapsat PWM do PCA9633 při prvním volání update().

Neřešíme reverzní ochranu ani časování – pouze ověřujeme,
že přímé nastavení PWM funguje správně.
"""

import unittest
from code import Wheel, DirectionEnum, PCA9633, I2C
from picoed import FakeI2C


class TestWheelApplyPwm(unittest.TestCase):
    """Testy přímé aplikace PWM bez reverzní logiky."""

    def test_apply_pwm_without_reverse(self):
        """
        Ověříme, že pokud se nemění směr,
        Wheel.update() okamžitě zapíše PWM do PCA9633.
        """

        hw = FakeI2C()
        wheel = Wheel(DirectionEnum.LEFT, PCA9633(I2C(hw)))

        wheel.ridePwm(100)
        wheel.update()

        # poslední zápis musí být PWM = 100
        self.assertEqual(hw.writes[-1][1][-1], 100)
