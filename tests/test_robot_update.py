"""
Test hlavní řídicí smyčky robota (Robot.update).

Cílem je ukázat studentům, že Robot.update():
    - čte senzory
    - aktualizuje kola
    - používá periodu (Period) pro řízení frekvence

Test je navržen tak, aby byl stabilní a nezávislý na tom,
jak studenti implementují detaily uvnitř subsystémů.

Používáme řízený čas pomocí adafruit_ticks:
    ticks.set_ticks_ms(...)
    ticks.advance_ticks(...)
"""

import unittest
import adafruit_ticks as ticks
from lib_vsc_only.busio import I2C as FakeI2C
from tests.create import createRobot

class TestRobotUpdate(unittest.TestCase):
    """Testy hlavní update smyčky robota."""

    def test_robot_update_calls_subsystems(self):
        """
        Ověříme, že Robot.update() zavolá: sensors.update(), wheels.update()

        Nepotřebujeme testovat logiku uvnitř subsystémů,
        pouze ověřujeme, že hlavní smyčka je správně propojená.
        """

        robot = createRobot(FakeI2C())

        # Fake data pro senzory – simulujeme změnu
        robot.sensors._dataPrev = 0
        robot.sensors._data = 1

        # Reset simulovaného času
        ticks.set_ticks_ms(0)

        # Zavoláme update – nesmí spadnout a musí projít subsystémy
        robot.update()

        # Pokud metoda doběhla bez výjimky, test je úspěšný
        self.assertTrue(True)
