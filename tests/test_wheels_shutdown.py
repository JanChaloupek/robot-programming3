"""
Test nouzového zastavení kol (Wheels.emergencyShutdown).

Cílem je ukázat studentům dvě věci:

1) Pokud všechna kola fungují správně,
   emergencyShutdown() musí zavolat stop() na každém kole.

2) Pokud některé kolo selže (vyhodí výjimku),
   emergencyShutdown() musí tuto výjimku propagovat dál.
   To je důležité pro bezpečnost – robot se nesmí tvářit,
   že je vše v pořádku, když jedno kolo nereaguje.

Používáme FakeWheel, který simuluje úspěch nebo selhání.
"""

import unittest
from _stubs.busio import I2C as FakeI2C
from tests.create import createWheels



class FakeWheel:
    """
    Jednoduchá falešná implementace kola.
    - stop() nastaví příznak stopped = True
    - pokud je should_fail=True, stop() vyhodí RuntimeError
    """
    def __init__(self, should_fail=False):
        self.stopped = False
        self.should_fail = should_fail

    def stop(self):
        if self.should_fail:
            raise RuntimeError("Wheel failure")
        self.stopped = True

class TestEmergencyShutdown(unittest.TestCase):
    """Testy nouzového zastavení všech kol."""

    def test_shutdown_success(self):
        """Ověříme, že pokud žádné kolo neselže, emergencyShutdown() zastaví obě kola."""
        hw_i2c = FakeI2C()
        wheels = createWheels(hw_i2c)

        wheels._wheels = {
            "left": FakeWheel(),
            "right": FakeWheel()
        }

        wheels.emergencyShutdown()

        self.assertTrue(wheels._wheels["left"].stopped)
        self.assertTrue(wheels._wheels["right"].stopped)

    def test_shutdown_with_failure(self):
        """Ověříme, že pokud jedno kolo selže, emergencyShutdown() vyhodí výjimku RuntimeError."""
        hw_i2c = FakeI2C()
        wheels = createWheels(hw_i2c)

        wheels._wheels = {
            "left": FakeWheel(),
            "right": FakeWheel(should_fail=True)
        }

        with self.assertRaises(RuntimeError):
            wheels.emergencyShutdown()
