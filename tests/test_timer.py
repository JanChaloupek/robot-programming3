"""
Testy pro Timer a Period – verze s řízeným časem přes adafruit_ticks.

Tyto testy ukazují studentům, jak správně simulovat čas v embedded projektech.
Místo hackování interních proměnných (např. _startTime) používáme funkce:

    ticks.set_ticks_ms(value)
    ticks.advance_ticks(delta)

Díky tomu testy přesně odpovídají tomu, jak Timer a Period fungují
na reálném MicroPython zařízení.
"""

import unittest
import adafruit_ticks as ticks
from code import Timer, Period


class TestTimer(unittest.TestCase):
    """
    Testy pro třídu Timer.

    Timer slouží k měření jednorázového timeoutu.
    - start(timeout_ms) nastaví nový časovač
    - isTimeout() vrací True, pokud čas vypršel
    """

    def test_timeout(self):
        """Timer by měl vypršet po uplynutí timeoutu."""
        ticks.set_ticks_ms(0)
        t = Timer(timeout_ms=100)   # startuje automaticky

        ticks.advance_ticks(50)
        self.assertFalse(t.isTimeout(), "Po 50 ms ještě timeout nenastal")

        ticks.advance_ticks(60)
        self.assertTrue(t.isTimeout(), "Po 110 ms už timeout nastal")

    def test_not_started(self):
        """Timer, který nebyl spuštěn, nikdy nevyprší."""
        t = Timer(startTimer=False)
        self.assertFalse(t.isTimeout(), "Timer bez startu nesmí vypršet")


class TestPeriod(unittest.TestCase):
    """
    Testy pro třídu Period.

    Period slouží k periodickému spouštění úloh.
    - ready() nebo isTime() vrací True, když uplynula perioda
    - po každém True se perioda automaticky resetuje
    """

    def test_period_resets(self):
        """Period by měl vrátit True po uplynutí periody a zároveň se resetovat."""
        ticks.set_ticks_ms(0)
        p = Period(timeout_ms=100)

        # 1. cyklus – ještě ne
        ticks.advance_ticks(50)
        self.assertFalse(p.isTime(), "Po 50 ms ještě perioda nevypršela")

        # 2. cyklus – perioda vyprší
        ticks.advance_ticks(60)
        self.assertTrue(p.isTime(), "Po 110 ms perioda vypršela")

        # 3. cyklus – ověříme, že se perioda resetovala
        ticks.advance_ticks(50)
        self.assertFalse(p.isTime(), "Po resetu musí perioda znovu čekat")

        ticks.advance_ticks(60)
        self.assertTrue(p.isTime(), "Po dalších 110 ms perioda opět vypršela")
