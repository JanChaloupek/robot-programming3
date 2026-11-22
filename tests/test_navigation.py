"""
test_navigation.py – Testy pro navigační modul a průjezd křižovatkami (CrossRoadsSM).

Výukový modul:
Ukazuje studentům, jak simulovat celou autonomní jízdu robota přes stavový automat
včetně přepínání senzorů na křižovatce bez reálného hardwaru.
"""

import unittest
from busio import I2C as FakeI2C
from tests.create import createRobot
from joycar.navigation import Commands, CrossRoadsSM
from joycar.direction import DirectionEnum
from joycar.sm import CPU
import _fake.adafruit_ticks as fake_ticks


class TestNavigation(unittest.TestCase):
    """Testovací sada pro navigační stavový automat křižovatek."""

    def setUp(self):
        CPU.clear()
        fake_ticks.set_ticks_ms(0)

    def test_commands_queue(self):
        """Ověří, že třída Commands správně prochází zadané instrukce trasy."""
        cmds = Commands([DirectionEnum.FORWARD, DirectionEnum.LEFT])

        self.assertEqual(len(cmds), 2)
        self.assertEqual(cmds.get(), DirectionEnum.FORWARD)

        cmds.next()
        self.assertEqual(cmds.get(), DirectionEnum.LEFT)

        cmds.next()
        self.assertIsNone(cmds.get(), "Po projetí všech příkazů musí get() vrátit None")

        cmds.reset()
        self.assertEqual(cmds.get(), DirectionEnum.FORWARD)

    def test_crossroads_mission_flow(self):
        """
        Kompletní simulace projetí křižovatky:
        1. Robot začne na přímé čáře (střední senzor 0b00001000).
        2. Přijede na křižovatku (všechny senzory 0b00011100).
        3. Příkaz je odbočit vlevo (DirectionEnum.LEFT).
        4. Robot popojede rovně (vycentrování osy).
        5. Robot začne točit vlevo na místě.
        6. Po odtočení střední senzor zachytí novou čáru.
        7. Trasa je u konce -> automat úspěšně končí v 'end'.
        """
        hw = FakeI2C()
        # 1. Počáteční stav: robot je na čáře
        hw.queue_read([0b00001000])
        robot = createRobot(hw)

        # Trasa o jednom příkazu: otočit vlevo
        cmds = Commands([DirectionEnum.LEFT])
        sm = CrossRoadsSM(robot, commands=cmds)
        CPU.add(sm)

        # Provedeme úvodní start a nastartování
        for _ in range(10):
            fake_ticks.advance_ticks(100)
            CPU.tick()

        self.assertIn('start', sm.history)
        self.assertIn('nastartuj', sm.history)
        self.assertIn('sleduj_caru', sm.history)

        # Simulujeme, že robot dorazil na křižovatku (všechny senzory sepnou)
        hw.queue_read([0b00011100])
        robot.sensors.updateSensorData()

        # Tik pro detekci křižovatky v sleduj_caru
        fake_ticks.advance_ticks(20)
        CPU.tick()
        fake_ticks.advance_ticks(20)
        CPU.tick()

        self.assertIn('krizovatka_left', sm.history)

        # Křižovatka má Step('krizovatka', tick_time=500)
        # Čekáme na uplynutí 500 ms a přechod do popojed
        for _ in range(6):
            fake_ticks.advance_ticks(100)
            CPU.tick()

        self.assertIn('popojed', sm.history)

        # Popojetí trvá 300 ms -> posuneme čas a vykonáme tiky
        for _ in range(5):
            fake_ticks.advance_ticks(100)
            CPU.tick()

        self.assertIn('zatoc', sm.history)

        # V otočení: nejprve běží ochranný turnErrorTimer (350 ms)
        fake_ticks.advance_ticks(400)
        # Nyní střední senzor najde novou čáru!
        hw.queue_read([0b00001000])
        robot.sensors.updateSensorData()

        # Tiky pro zachycení čáry a návrat do sleduj_caru -> detekce konce trasy -> end
        for _ in range(6):
            fake_ticks.advance_ticks(50)
            CPU.tick()

        self.assertIn('end', sm.history)
        self.assertTrue(sm.success)
        self.assertFalse(CPU.existSM(), "Dokončený automat musí být vyřazen z CPU")


if __name__ == "__main__":
    unittest.main()
