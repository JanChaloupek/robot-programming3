"""
Test reverzní ochrany jednoho kola (Wheel).

Tento test je navržen tak, aby fungoval i v případě,
že studenti změní reverzní timeout (např. z 100 ms na 1000 ms).

Používáme dvě hranice:
    reverse_timeout_min – čas, kdy timeout ještě nesmí vypršet
    reverse_timeout_max – čas, kdy timeout už musí vypršet

Tím zajistíme robustní chování testu bez ohledu na studentské úpravy.

Reverzní sekvence:
    1) první update → STOP (PWM = 0)
    2) čekání na reverzní timeout
    3) druhý update → aplikace nového PWM

Čas simulujeme pomocí adafruit_ticks:
    ticks.set_ticks_ms(...)
    ticks.advance_ticks(...)
"""

import unittest
import adafruit_ticks as ticks
from joycar import DirectionEnum
from _stubs.busio import I2C as FakeI2C
from tests.create import createWheel

class TestWheelReverse(unittest.TestCase):
    """Testy reverzní ochrany jednoho kola."""

    def setUp(self):
        """Každý test začíná čistým FakeI2C a novým kolem."""
        self.hw = FakeI2C()
        self.wheel = createWheel(self.hw, DirectionEnum.LEFT)

    def test_reverse_sequence(self):
        """
        Ověříme kompletní reverzní sekvenci: \
        - dopředu → STOP → čekání → dozadu \
        - test funguje i při změně reverzního timeoutu studenty
        """

        # Reverzní timeout – robustní hranice
        reverse_timeout_min = 50     # ještě nesmí vypršet
        reverse_timeout_max = 1200   # už musí vypršet

        # ---------------------------------------------------------
        # 1) Rozjeď dopředu
        # ---------------------------------------------------------
        ticks.set_ticks_ms(0)
        self.wheel.setSpeed(100)
        self.wheel.update()

        # poslední zápis musí být PWM=100
        self.assertEqual(self.hw.write_history[-1][1][-1], 100)

        # ---------------------------------------------------------
        # 2) Požaduj reverz (dopředu → dozadu)
        # ---------------------------------------------------------
        self.wheel.setSpeed(-100)
        self.wheel.update()

        # první krok reverzu = STOP
        self.assertEqual(self.hw.write_history[-1][1][-1], 0)

        # ---------------------------------------------------------
        # 3) Timer ještě nevypršel → stále STOP
        # ---------------------------------------------------------
        ticks.advance_ticks(reverse_timeout_min)
        self.wheel.update()
        self.assertEqual(self.hw.write_history[-1][1][-1], 0)

        # ---------------------------------------------------------
        # 4) Simuluj vypršení reverzního timeoutu
        # ---------------------------------------------------------
        ticks.advance_ticks(reverse_timeout_max)
        self.wheel.update()

        # ---------------------------------------------------------
        # 5) Teď se musí aplikovat nový PWM
        # ---------------------------------------------------------
        self.assertEqual(self.hw.write_history[-1][1][-1], 100)  # |-100| = 100
