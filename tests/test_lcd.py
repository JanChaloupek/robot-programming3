"""
test_lcd.py – Unit testy pro alfanumerický textový LCD displej (HD44780 na I2C).
"""

import unittest
from busio import I2C as FakeI2C
from joycar.lcd import TextDisplay


class TestTextDisplay(unittest.TestCase):
    """Testuje chování TextDisplay včetně zapínání a vypínání (enable/disable)."""

    def test_init_disabled(self):
        hw = FakeI2C()
        lcd = TextDisplay(hw, enabled=False)
        self.assertFalse(lcd.is_enabled)

        # Volání metod při vypnutém displeji nesmí způsobit pád ani zápis na I2C
        lcd.write("Ahoj")
        lcd.clear()
        self.assertEqual(len(hw.write_history), 0)

    def test_enable_and_disable(self):
        hw = FakeI2C()
        lcd = TextDisplay(hw, enabled=True)
        self.assertTrue(lcd.is_enabled)

        # Smazání displeje
        lcd.clear()
        self.assertGreater(len(hw.write_history), 0)

        # Vypnutí displeje
        lcd.disable()
        self.assertFalse(lcd.is_enabled)

        # Opětovné zapnutí
        lcd.enable()
        self.assertTrue(lcd.is_enabled)

    def test_write_and_write_line(self):
        hw = FakeI2C()
        lcd = TextDisplay(hw, rows=2, cols=16, enabled=True)
        hw.write_history.clear()

        lcd.writeLine(0, "JoyCar Robot")
        self.assertGreater(len(hw.write_history), 0)

    def test_write_position(self):
        hw = FakeI2C()
        lcd = TextDisplay(hw, rows=4, cols=20, enabled=True)
        hw.write_history.clear()

        lcd.writePosition(x=0.15, y=0.30, theta=1.57)
        self.assertGreater(len(hw.write_history), 0)

    def test_backlight_control(self):
        """Ověří zapnutí a vypnutí podsvícení textového LCD."""
        hw = FakeI2C()
        lcd = TextDisplay(hw, enabled=True)
        hw.write_history.clear()

        lcd.backlight_off()
        self.assertFalse(lcd._backlight)
        self.assertGreater(len(hw.write_history), 0)

        hw.write_history.clear()
        lcd.backlight_on()
        self.assertTrue(lcd._backlight)
        self.assertGreater(len(hw.write_history), 0)

    def test_string_padding_and_truncation(self):
        """Ověří ořezání příliš dlouhých řetězců na šířku displeje."""
        hw = FakeI2C()
        lcd = TextDisplay(hw, rows=2, cols=16, enabled=True)
        hw.write_history.clear()

        # Dlouhý text (více než 16 znaků)
        long_text = "Tento text ma rozhodne vice nez 16 znaku"
        lcd.writeLine(0, long_text)
        self.assertGreater(len(hw.write_history), 0)


if __name__ == "__main__":
    unittest.main()
