"""
Test přímé aplikace PWM na jedno kolo (Wheel) bez reverzní sekvence.

Tento test ukazuje studentům základní chování:
pokud se nemění směr (např. 0 → +100), Wheel musí okamžitě
zapsat PWM do PCA9633 při prvním volání update().

Neřešíme reverzní ochranu ani časování – pouze ověřujeme,
že přímé nastavení PWM funguje správně.
"""

import unittest
from joycar import DirectionEnum
from _stubs.busio import I2C as FakeI2C
from tests.create import createWheel

class TestWheelApplyPwm(unittest.TestCase):
    """Testy přímé aplikace PWM bez reverzní logiky."""

    def test_apply_pwm_without_reverse(self):
        """Ověříme, že pokud  createWheelse nemění směr, Wheel.update() okamžitě zapíše PWM do PCA9633."""

        hw = FakeI2C()
        wheel = createWheel(hw, DirectionEnum.LEFT)
        wheel.setSpeed(100)
        wheel.update()

        # poslední zápis musí být PWM = 100
        self.assertEqual(hw.write_history[-1][1][-1], 100)