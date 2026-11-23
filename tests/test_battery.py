"""
test_battery.py – Unit testy pro měření napětí baterie robota JoyCar.
"""

import unittest
from analogio import AnalogIn
from joycar.battery import battery_voltage


class TestBattery(unittest.TestCase):
    """Testovací sada pro měření napětí baterie na pinu P2."""

    def tearDown(self):
        AnalogIn.default_value = 0

    def test_battery_voltage_usb_or_simulator_returns_none(self):
        """Při běhu na USB nebo odpojené baterii (ADC < 500) vrací None."""
        AnalogIn.default_value = 120
        self.assertIsNone(battery_voltage())

    def test_battery_voltage_calculated_correctly(self):
        """Pro reálné napětí baterie (např. ADC 32653) vrátí cca 4.80 V."""
        AnalogIn.default_value = 32653
        v = battery_voltage()
        self.assertIsNotNone(v)
        # 32653 * 0.000147 = 4.799991 V
        self.assertAlmostEqual(v, 4.80, delta=0.02)

    def test_battery_voltage_boundary_conditions(self):
        """Hraniční test těsně pod a nad prahem 500."""
        # 499 < 500 -> None
        AnalogIn.default_value = 499
        self.assertIsNone(battery_voltage())

        # 500 >= 500 -> 500 * 0.000147 = 0.0735 V
        AnalogIn.default_value = 500
        v = battery_voltage()
        self.assertIsNotNone(v)
        self.assertAlmostEqual(v, 0.0735, delta=0.001)


if __name__ == "__main__":
    unittest.main()
