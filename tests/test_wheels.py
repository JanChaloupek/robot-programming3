"""
Test základní struktury třídy Wheels.

Cílem je ukázat studentům, že objekt Wheels musí vždy
obsahovat dvě kola:
    - levé kolo (left)
    - pravé kolo (right)

Tento test neřeší reverzní logiku ani PWM.
Pouze ověřuje, že konstruktor správně vytvoří obě kola.
"""

import unittest
from lib_vsc_only.busio import I2C as FakeI2C
from tests.create import createWheels

class TestWheels(unittest.TestCase):
    """Testy základní struktury objektu Wheels."""

    def test_left_right(self):
        """
        Ověříme, že Wheels po vytvoření obsahuje atributy left a right, které nejsou None.
        """
        w = createWheels(FakeI2C())

        self.assertIsNotNone(w.left)
        self.assertIsNotNone(w.right)
