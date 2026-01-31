"""
Test normalizace PWM v třídě Wheel.

Tento test ověřuje dvě klíčové části logiky:
    1) dead‑zone – malé hodnoty PWM se automaticky zvýší na minimální sílu
    2) maximální limit – příliš velké hodnoty se omezí na 255

Tyto testy pomáhají studentům pochopit, že Wheel nepracuje
s PWM přímo, ale nejprve ho normalizuje do bezpečného rozsahu.
"""

import unittest
from joycar import DirectionEnum
from busio import I2C as FakeI2C
from tests.create import createWheel

class TestWheel(unittest.TestCase):
    """Testy normalizace PWM v třídě Wheel."""

    def test_apply_deadzone(self):
        """Ověříme, že velmi malé PWM (např. 5) se zvýší na minimální hodnotu dead‑zony (např. 20)."""
        hw_i2c = FakeI2C()
        w = createWheel(hw_i2c, DirectionEnum.LEFT)

        w.setSpeed(5)

        self.assertEqual(w._targetPwm, 20)

    def test_max_limit(self):
        """Ověříme, že příliš velké PWM (např. 999) se omezí na maximální hodnotu 255."""
        hw = FakeI2C()
        w = createWheel(hw, DirectionEnum.LEFT)

        w.setSpeed(999)

        self.assertEqual(w._targetPwm, 255)
