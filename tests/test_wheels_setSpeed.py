"""
Test rozdělení PWM na dvě kola (Wheels) s reverzní ochranou.

Tento test ověřuje realistické chování:
    - setSpeed okamžitě aplikuje PWM, pokud se nemění znaménko
    - reverzní STOP se spustí pouze u kol, která mění směr
    - po reverzní ochranné době se aplikují nové PWM hodnoty

Test je navržen tak, aby fungoval i v případě,
že studenti změní reverzní timeout (např. z 100 ms na 1000 ms).

Používáme dvě hranice:
    reverse_timeout_min – čas, kdy timeout ještě nesmí vypršet
    reverse_timeout_max – čas, kdy timeout už musí vypršet

Čas simulujeme pomocí adafruit_ticks:
    ticks.set_ticks_ms(...)
    ticks.advance_ticks(...)
"""

import unittest
import adafruit_ticks as ticks
from busio import I2C as FakeI2C
from tests.create import createWheels

class TestWheelsSetSpeed(unittest.TestCase):
    """Testy správného rozdělení PWM na dvě kola podle realistického modelu."""

    def test_set_speed_assigns_correctly(self):
        """
        Ověříme, že: \
        - setSpeed okamžitě aplikuje PWM, pokud se nemění znaménko \
        - reverzní STOP se spustí pouze u kol, která mění směr \
        - po vypršení reverzního timeoutu se aplikují nové PWM hodnoty
        """

        hw_i2c = FakeI2C()
        wheels = createWheels(hw_i2c)

        reverse_timeout_min = 50     # ještě nesmí vypršet
        reverse_timeout_max = 1200   # už musí vypršet

        # ---------------------------------------------------------
        # 1) Požaduj PWM pro obě kola (0 → 100 a 0 → -50)
        #    → podle modelu se má PWM aplikovat okamžitě
        # ---------------------------------------------------------
        ticks.set_ticks_ms(0)
        wheels.setSpeed({"left": 100, "right": -50})

        # Najdeme poslední nenulové PWM hodnoty
        nonzero_pwms = [w[1][1] for w in hw_i2c.write_history if w[1][1] != 0]

        self.assertIn(100, nonzero_pwms)   # levé kolo
        self.assertIn(50, nonzero_pwms)    # pravé kolo (|-50| = 50)

        # ---------------------------------------------------------
        # 2) První update() → nemění se znaménko → žádný reverz
        # ---------------------------------------------------------
        wheels.update()

        nonzero_pwms = [w[1][1] for w in hw_i2c.write_history if w[1][1] != 0]
        self.assertIn(100, nonzero_pwms)
        self.assertIn(50, nonzero_pwms)

        # ---------------------------------------------------------
        # 3) Změna znaménka → reverzní STOP pouze u kol, která mění směr
        # ---------------------------------------------------------
        wheels.setSpeed({"left": -80, "right": 30})   # levé: 100 → -80, pravé: -50 → 30

        wheels.update()  # první update po reverzu = STOP
        last_pwms = [w[1][1] for w in hw_i2c.write_history[-2:]]
        self.assertEqual(last_pwms, [0, 0])

        # ---------------------------------------------------------
        # 4) Reverzní timeout ještě nevypršel → stále STOP
        # ---------------------------------------------------------
        ticks.advance_ticks(reverse_timeout_min)
        wheels.update()

        last_pwms = [w[1][1] for w in hw_i2c.write_history[-2:]]
        self.assertEqual(last_pwms, [0, 0])

        # ---------------------------------------------------------
        # 5) Reverzní timeout vypršel → aplikuj nové PWM
        # ---------------------------------------------------------
        ticks.advance_ticks(reverse_timeout_max)
        wheels.update()

        nonzero_pwms = [w[1][1] for w in hw_i2c.write_history if w[1][1] != 0]

        self.assertIn(80, nonzero_pwms)   # levé kolo (|-80| = 80)
        self.assertIn(30, nonzero_pwms)   # pravé kolo
