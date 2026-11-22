"""
test_robot_integration.py – Integrační testy pro hlavní řídicí třídu JoyCarRobot.

Výukový modul:
Ověřuje propojení senzorů, motorů a světel přes superloop metodu robot.update(),
chování rideLine() pro sledování čáry a bezpečnostní vypnutí robot.stop().
"""

import unittest
from busio import I2C as FakeI2C
from tests.create import createRobot
from joycar.sensors import LineSituationEnum, CrossRoadType
from joycar.lights import BeamsEnum
import _fake.adafruit_ticks as fake_ticks


class TestRobotIntegration(unittest.TestCase):
    """Testovací sada pro integraci subsystémů v JoyCarRobot."""

    def setUp(self):
        fake_ticks.set_ticks_ms(0)

    def test_robot_has_all_subsystems(self):
        """Ověří, že robot má správně inicializovány senzory, kola i světla."""
        hw = FakeI2C()
        robot = createRobot(hw)

        self.assertIsNotNone(robot.sensors)
        self.assertIsNotNone(robot.wheels)
        self.assertIsNotNone(robot.lights)

    def test_rideline_straight(self):
        """Když je čára pod středním senzorem (direction == 0), robot jede přímo vpřed."""
        hw = FakeI2C()
        # Střední senzor aktivní (raw bit 3 = 1) -> 0b00001000
        hw.queue_read([0b00001000])
        robot = createRobot(hw)

        robot.rideLine(baseSpeed=0.25, turnGain=0.5)

        self.assertEqual(robot._linearSpeed, 0.25)
        self.assertEqual(robot._angularSpeed, 0.0)

    def test_rideline_turn_left(self):
        """Když je čára vlevo (direction > 0), úhlová rychlost omega musí být kladná."""
        hw = FakeI2C()
        # Levý senzor aktivní (raw bit 2 = 1) -> 0b00000100 -> direction == 3
        hw.queue_read([0b00000100])
        robot = createRobot(hw)

        robot.rideLine(baseSpeed=0.2, turnGain=0.5)

        self.assertEqual(robot._linearSpeed, 0.2)
        # omega = 3 * 0.5 = 1.5 rad/s
        self.assertAlmostEqual(robot._angularSpeed, 1.5)

    def test_rideline_turn_right(self):
        """Když je čára vpravo (direction < 0), úhlová rychlost omega musí být záporná."""
        hw = FakeI2C()
        # Pravý senzor aktivní (raw bit 4 = 1) -> 0b00010000 -> direction == -3
        hw.queue_read([0b00010000])
        robot = createRobot(hw)

        robot.rideLine(baseSpeed=0.2, turnGain=0.5)

        self.assertEqual(robot._linearSpeed, 0.2)
        # omega = -3 * 0.5 = -1.5 rad/s
        self.assertAlmostEqual(robot._angularSpeed, -1.5)

    def test_rideline_out_of_line_ignored(self):
        """Pokud robot nevidí čáru (direction is None), rideLine nemění rychlosti."""
        hw = FakeI2C()
        hw.queue_read([0b00000000])  # Žádný senzor
        robot = createRobot(hw)

        robot._linearSpeed = 0.1
        robot._angularSpeed = 0.0
        robot.rideLine(baseSpeed=0.2, turnGain=0.5)

        # Rychlosti zůstaly nezměněny
        self.assertEqual(robot._linearSpeed, 0.1)
        self.assertEqual(robot._angularSpeed, 0.0)

    def test_stop_activates_brake_lights(self):
        """Volání robot.stop() zastaví podvozek a aktivuje brzdová světla."""
        hw = FakeI2C()
        robot = createRobot(hw)

        # Jedeme dopředu
        robot.setVelocity(0.3, 0.0)
        robot.update()
        self.assertFalse(robot.lights.isBraking())

        # Zastavíme
        fake_ticks.advance_ticks(100)
        robot.stop()
        self.assertEqual(robot._linearSpeed, 0.0)
        self.assertEqual(robot._angularSpeed, 0.0)
        self.assertTrue(robot.lights.isBraking())

    def test_emergency_shutdown(self):
        """Nouzové zastavení vypne motory i světla."""
        hw = FakeI2C()
        robot = createRobot(hw)

        robot.lights.mainBeams = BeamsEnum.HIGH
        robot.emergencyShutdown()

        self.assertEqual(robot._linearSpeed, 0.0)
        self.assertEqual(robot.lights.mainBeams, BeamsEnum.OFF)


if __name__ == "__main__":
    unittest.main()
