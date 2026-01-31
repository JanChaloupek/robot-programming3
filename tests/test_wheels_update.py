"""
Test volání update() na všech kolech v objektu Wheels.

Tento test je jednoduchý, ale pro studenty velmi důležitý:
ukazuje, že metoda Wheels.update() musí zavolat update() na
každém kole, které Wheels spravuje.

Používáme FakeWheel, který si pouze zapamatuje,
zda jeho update() bylo zavoláno.
"""

import unittest
from busio import I2C as FakeI2C
from tests.create import createWheels


class FakeWheel:
    """
    Jednoduchá falešná implementace kola.
    Slouží pouze k ověření, že Wheels.update()
    skutečně zavolá update() na všech kolech.
    """
    def __init__(self):
        self.updated = False

    def update(self):
        self.updated = True


class TestWheelsUpdate(unittest.TestCase):
    """Testy správného volání update() na všech kolech."""

    def test_update_calls_both_wheels(self):
        """
        Ověříme, že Wheels.update() zavolá update() na levém i pravém kole.

        Tento test neřeší reverzní logiku ani PWM,
        pouze ověřuje správnou strukturu volání.
        """

        hw = FakeI2C()
        wheels = createWheels(hw)

        # Nahradíme skutečná kola jednoduchými FakeWheel objekty
        wheels._wheels = {
            "left": FakeWheel(),
            "right": FakeWheel()
        }

        wheels.update()

        self.assertTrue(wheels._wheels["left"].updated)
        self.assertTrue(wheels._wheels["right"].updated)
