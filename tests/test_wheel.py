"""
Test normalizace PWM v třídě Wheel.

Tento test ověřuje dvě klíčové části logiky:
    1) dead‑zone – malé hodnoty PWM se automaticky zvýší na minimální sílu
    2) maximální limit – příliš velké hodnoty se omezí na 255

Tyto testy pomáhají studentům pochopit, že Wheel nepracuje
s PWM přímo, ale nejprve ho normalizuje do bezpečného rozsahu.
"""

import unittest
from code import Wheel, DirectionEnum, PCA9633, I2C
from picoed import FakeI2C


class TestWheel(unittest.TestCase):
    """Testy normalizace PWM v třídě Wheel."""

    def test_apply_deadzone(self):
        """
        Ověříme, že velmi malé PWM (např. 5) se zvýší
        na minimální hodnotu dead‑zony (např. 20).
        """
        hw = FakeI2C()
        w = Wheel(DirectionEnum.LEFT, PCA9633(I2C(hw)))

        w.ridePwm(5)

        self.assertEqual(w._targetPwm, 20)

    def test_max_limit(self):
        """
        Ověříme, že příliš velké PWM (např. 999)
        se omezí na maximální hodnotu 255.
        """
        hw = FakeI2C()
        w = Wheel(DirectionEnum.LEFT, PCA9633(I2C(hw)))

        w.ridePwm(999)

        self.assertEqual(w._targetPwm, 255)
