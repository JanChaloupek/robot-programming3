"""
test_heartbeat.py – Unit testy pro LEDku života (Heartbeat LED).

Ověřuje:
1. Automatické periodické blikání stavové LED (150 ms) během běhu hlavní smyčky Superloop.
2. Správnou funkci vypnutí LEDky života přes vlastnost heartbeat_enabled.
3. Bezpečné zhasnutí LEDky života při nouzovém zastavení emergencyShutdown().
"""

import unittest
from busio import I2C as FakeI2C
import _fake.adafruit_ticks as fake_ticks
from _fake.picoed import led as fake_led
from joycar import JoyCarRobot, I2C


class TestHeartbeatLED(unittest.TestCase):
    """Testovací sada pro LEDku života (Heartbeat LED)."""

    def setUp(self):
        fake_ticks.set_ticks_ms(0)
        fake_led.off()
        fake_led.state_history.clear()

    def test_heartbeat_enabled_by_default(self):
        """Ověří, že LEDka života je ve výchozím stavu aktivní."""
        hw = FakeI2C()
        robot = JoyCarRobot(I2C(hw))
        self.assertTrue(robot.heartbeat_enabled)

    def test_heartbeat_blinking_on_update(self):
        """Ověří, že robot.update() přepíná LED v periodě 150 ms."""
        hw = FakeI2C()
        robot = JoyCarRobot(I2C(hw))

        # Čas 0 ms: první takt, perioda teprve začíná
        robot.update()
        self.assertEqual(len(fake_led.state_history), 0)

        # Čas 100 ms (< 150 ms): ještě neuplynula perioda, LED se nepřepne
        fake_ticks.set_ticks_ms(100)
        robot.update()
        self.assertEqual(len(fake_led.state_history), 0)

        # Čas 155 ms (>= 150 ms): perioda vypršela -> LED se přepne (toggle True)
        fake_ticks.set_ticks_ms(155)
        robot.update()
        self.assertEqual(len(fake_led.state_history), 1)
        self.assertTrue(fake_led.is_on)

        # Čas 200 ms: mezidobí, žádná změna
        fake_ticks.set_ticks_ms(200)
        robot.update()
        self.assertEqual(len(fake_led.state_history), 1)

        # Čas 310 ms (>= 155 + 150 ms): další perioda -> LED se přepne zpět (toggle False)
        fake_ticks.set_ticks_ms(310)
        robot.update()
        self.assertEqual(len(fake_led.state_history), 2)
        self.assertFalse(fake_led.is_on)

    def test_heartbeat_disable(self):
        """Ověří, že při heartbeat_enabled = False LED nebliká a zhasne."""
        hw = FakeI2C()
        robot = JoyCarRobot(I2C(hw))

        # Zapneme LEDku přes update
        fake_ticks.set_ticks_ms(155)
        robot.update()
        self.assertTrue(fake_led.is_on)

        # Deaktivujeme heartbeat
        robot.heartbeat_enabled = False
        self.assertFalse(robot.heartbeat_enabled)
        self.assertFalse(fake_led.is_on)

        # Další tiky už stav LED nezmění
        fake_ticks.set_ticks_ms(350)
        robot.update()
        self.assertFalse(fake_led.is_on)

    def test_heartbeat_emergency_shutdown(self):
        """Ověří, že při emergencyShutdown() se LEDka života okamžitě zhasne."""
        hw = FakeI2C()
        robot = JoyCarRobot(I2C(hw))

        # Přivedeme LED do rozsvíceného stavu
        fake_ticks.set_ticks_ms(155)
        robot.update()
        self.assertTrue(fake_led.is_on)

        # Nouzové zastavení zhasne LED
        robot.emergencyShutdown()
        self.assertFalse(fake_led.is_on)


if __name__ == "__main__":
    unittest.main()
