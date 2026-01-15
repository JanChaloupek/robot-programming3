"""
Test sanitizace PWM v třídě Wheel.

Metoda _sanitizePwm() převádí vstupní PWM na bezpečnou hodnotu.
Ověřujeme tyto pravidla:

1) Hodnota 0 zůstává 0.
2) Malé hodnoty se zvýší na dead‑zone (např. 5 → 20).
3) Velké hodnoty se omezí na maximum 255.
4) Stejná logika platí i pro záporné hodnoty.

Tento test pomáhá studentům pochopit, že Wheel
nikdy nepoužívá PWM přímo, ale vždy ho nejprve normalizuje.
"""

import unittest
from code import Wheel, DirectionEnum, PCA9633, I2C
from picoed import FakeI2C


class TestWheelSanitize(unittest.TestCase):
    """Testy normalizace PWM pomocí _sanitizePwm()."""

    def setUp(self):
        self.hw = FakeI2C()
        self.wheel = Wheel(DirectionEnum.LEFT, PCA9633(I2C(self.hw)))

    def test_zero_stays_zero(self):
        """Hodnota 0 musí zůstat 0."""
        self.assertEqual(self.wheel._sanitizePwm(0), 0)

    def test_deadzone_applied(self):
        """Malé hodnoty se musí zvýšit na dead‑zone."""
        self.assertEqual(self.wheel._sanitizePwm(5), 20)

    def test_max_limit_applied(self):
        """Příliš velké hodnoty se musí omezit na 255."""
        self.assertEqual(self.wheel._sanitizePwm(999), 255)

    def test_negative_deadzone(self):
        """Záporné malé hodnoty se musí zvýšit na zápornou dead‑zone."""
        self.assertEqual(self.wheel._sanitizePwm(-10), -20)

    def test_negative_max_limit(self):
        """Záporné velké hodnoty se musí omezit na -255."""
        self.assertEqual(self.wheel._sanitizePwm(-999), -255)
