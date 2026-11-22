"""
test_lights.py – Testy pro světelný subsystém (LightsControl a Indicator).

Výukový modul:
Ověřuje správné neblokující časování blinkrů, přepínání dálkových/potkávacích světel
a automatické brzdové světlo po zastavení.
"""

import unittest
from joycar.lights import LightsControl, Indicator, BeamsEnum
from joycar.direction import DirectionEnum
from neopixel import NeoPixel
import board
import _fake.adafruit_ticks as fake_ticks


class TestLightsControl(unittest.TestCase):
    """Testovací sada pro světla robota JoyCar."""

    def setUp(self):
        """Před každým testem resetujeme simulovaný čas a vytvoříme NeoPixel buffer."""
        fake_ticks.set_ticks_ms(0)
        self.pixel_buf = NeoPixel(board.P0, 8, auto_write=False)
        self.lights = LightsControl(neopixel_instance=self.pixel_buf)

    def test_indicator_left_blinking(self):
        """Ověří, že levý blinkr střídá stav po 400 ms (zapnuto / vypnuto)."""
        ind = Indicator(blinkIntervalMs=400)
        ind.direction = DirectionEnum.LEFT

        # Před startem je stav None
        self.assertIsNone(ind.indicatorLight)

        # 1. tik: zapne se na True
        ind.update()
        self.assertTrue(ind.indicatorLight)

        # Po 200 ms stále svítí
        fake_ticks.advance_ticks(200)
        ind.update()
        self.assertTrue(ind.indicatorLight)

        # Po dalších 250 ms (celkem 450 ms) se přepne na False (zhasne)
        fake_ticks.advance_ticks(250)
        ind.update()
        self.assertFalse(ind.indicatorLight)

        # Po dalších 400 ms se opět rozsvítí
        fake_ticks.advance_ticks(400)
        ind.update()
        self.assertTrue(ind.indicatorLight)

        # Vypnutí blinkru
        ind.direction = None
        ind.update()
        self.assertIsNone(ind.indicatorLight)

    def test_warning_lights_both_sides(self):
        """Výstražná světla musí aktivovat levou i pravou stranu současně."""
        ind = Indicator(blinkIntervalMs=400)
        ind.warning = True

        self.assertTrue(ind.isLeft())
        self.assertTrue(ind.isRight())

    def test_headlights_dipped_and_high(self):
        """Ověří rozsvícení potkávacích (tlumených) a dálkových světel."""
        # 1. Potkávací světla
        self.lights.mainBeams = BeamsEnum.DIPPED
        self.lights.update(force=True)

        # LED 0 a 3 musí být tlumeně bílé (60, 60, 60)
        self.assertEqual(self.pixel_buf[0], LightsControl.COLOR_WHITE_DIPPED)
        self.assertEqual(self.pixel_buf[3], LightsControl.COLOR_WHITE_DIPPED)
        # Zadní světla (5, 6) musí svítit červeně (60, 0, 0)
        self.assertEqual(self.pixel_buf[5], LightsControl.COLOR_RED_TAIL)
        self.assertEqual(self.pixel_buf[6], LightsControl.COLOR_RED_TAIL)

        # 2. Dálková světla
        self.lights.mainBeams = BeamsEnum.HIGH
        self.lights.update(force=True)

        # LED 0 a 3 musí být plně bílé (255, 255, 255)
        self.assertEqual(self.pixel_buf[0], LightsControl.COLOR_WHITE_HIGH)
        self.assertEqual(self.pixel_buf[3], LightsControl.COLOR_WHITE_HIGH)

    def test_brake_light_activation_and_timeout(self):
        """
        Ověří, že prudké zastavení z dopředné rychlosti rozsvítí brzdová světla (plná červená)
        a po 600 ms se vrátí zpět na obrysová světla.
        """
        self.lights.mainBeams = BeamsEnum.DIPPED
        self.lights.setForwardSpeed(0.5)  # Jede dopředu
        self.lights.update(force=True)

        # Zadní světla svítí běžnou obrysovou červenou
        self.assertEqual(self.pixel_buf[5], LightsControl.COLOR_RED_TAIL)
        self.assertFalse(self.lights.isBraking())

        # Robot zabrzdí na 0
        fake_ticks.set_ticks_ms(100)
        self.lights.setForwardSpeed(0.0)
        self.assertTrue(self.lights.isBraking())

        self.lights.update(force=True)
        # Nyní musí svítit plná brzdová červená (255, 0, 0)
        self.assertEqual(self.pixel_buf[5], LightsControl.COLOR_RED_BRAKE)
        self.assertEqual(self.pixel_buf[6], LightsControl.COLOR_RED_BRAKE)

        # Po 500 ms (čas 600 ms, od brzdění uběhlo 500 ms) stále brzdí
        fake_ticks.set_ticks_ms(600)
        self.assertTrue(self.lights.isBraking())

        # Po vypršení 600 ms od startu brzdění (čas 750 ms) brzdové světlo zhasne zpět na obrysové
        fake_ticks.set_ticks_ms(750)
        self.assertFalse(self.lights.isBraking())

        self.lights.update(force=True)
        self.assertEqual(self.pixel_buf[5], LightsControl.COLOR_RED_TAIL)

    def test_reversing_light(self):
        """Při záporné rychlosti (couvání) se levé zadní světlo rozsvítí bíle."""
        self.lights.setForwardSpeed(-0.2)
        self.assertTrue(self.lights.isReversing())

        self.lights.update(force=True)
        self.assertEqual(self.pixel_buf[5], LightsControl.COLOR_WHITE_REVERSE)

    def test_lights_off(self):
        """Metoda off() zhasne všechny diody."""
        self.lights.mainBeams = BeamsEnum.HIGH
        self.lights.update(force=True)
        self.assertNotEqual(self.pixel_buf[0], (0, 0, 0))

        self.lights.off()
        for i in range(8):
            self.assertEqual(self.pixel_buf[i], (0, 0, 0))


if __name__ == "__main__":
    unittest.main()
