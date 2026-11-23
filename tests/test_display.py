"""
test_display.py – Unit testy pro rychlý framebuffer maticového displeje Pico:ed (17×7 LED).
"""

import unittest
from busio import I2C as FakeI2C
from joycar.display import Display, display


class TestDisplay(unittest.TestCase):
    """Testovací sada pro Display (IS31FL3731 na Pico:ed)."""

    def test_display_singleton(self):
        """Ověří, že Display implementuje vzor Singleton."""
        d1 = Display()
        d2 = Display()
        self.assertIs(d1, d2)
        self.assertIs(display, d1)

    def test_display_pixel_addr(self):
        """Ověří výpočet hardwarového indexu pixelu pro levou a pravou polovinu."""
        d = Display()
        # Levá polovina (x <= 8)
        idx_left = d._pixelIndex(0, 0)
        self.assertIsInstance(idx_left, int)

        # Pravá polovina (x > 8)
        idx_right = d._pixelIndex(10, 0)
        self.assertIsInstance(idx_right, int)
        self.assertNotEqual(idx_left, idx_right)

    def test_display_fill_and_pixel(self):
        """Ověří nastavení pixelu a vyplnění framebufferu."""
        d = Display()
        # fill() provede výchozí vyčištění a automatický flush
        d.fill(0)
        self.assertFalse(d._needFlush)

        # Nastavení pixelu na souřadnicích (2, 3) s jasem 50 nastaví příznak _needFlush
        d.pixel(2, 3, 50)
        self.assertTrue(d._needFlush)

        # Flush odešle data na sběrnici a resetuje příznak
        d.flush()
        self.assertFalse(d._needFlush)

    def test_display_drive_mode_icons(self):
        """Ověří nastavení ikon režimu jízdy ('s' jako stop, 'x' jako chyba)."""
        d = Display()
        d.drive_mode('s')
        d.flush()

        d.drive_mode('x')
        d.flush()

    def test_display_number(self):
        """Ověří zobrazení číselné hodnoty (např. napětí baterie 48)."""
        d = Display()
        d.number(48)
        d.flush()


if __name__ == "__main__":
    unittest.main()
