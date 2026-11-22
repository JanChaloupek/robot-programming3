"""
test_sensors_line.py – Unit testy pro vyhodnocování čáry, křižovatek a překážek.

Výukový modul testů:
Tento testovací soubor ukazuje studentům, jak testovat logiku řízení robota na PC
bez nutnosti mít připojený fyzický hardware. Využívá k tomu FakeI2C simulátor sběrnice.
"""

import unittest
from busio import I2C as FakeI2C
from tests.create import createSensors
from joycar.sensors import Sensors, LineSituationEnum, CrossRoadType
import _fake.adafruit_ticks as fake_ticks


class TestSensorsLineFollowing(unittest.TestCase):
    """
    Testovací sada pro navigaci po čáře a detekci křižovatek.
    
    Připomenutí mapování bitů PCF8574 v surovém čtení:
    - LineLeft   = 0x04 (bit 2)
    - LineMiddle = 0x08 (bit 3)
    - LineRight  = 0x10 (bit 4)
    - ObstacleLeft  = 0x20 (bit 5)
    - ObstacleRight = 0x40 (bit 6)
    
    Když je čára pod senzorem, v surovém čtení je daný bit roven 1 (po následném XOR
    s maskou 0x1C je v interním registru roven 0 -> aktivní senzor).
    """

    def setUp(self):
        """Před každým testem resetujeme simulovaný čas na 0 ms."""
        fake_ticks.set_ticks_ms(0)

    def test_line_direction_center(self):
        """
        Ověří, že čára přesně uprostřed (pouze LineMiddle) vrací směr 0 (přímá jízda).
        Surový stav: bit 3 = 1 -> 0b00001000 = 0x08
        """
        hw = FakeI2C()
        hw.queue_read([0b00001000])
        s = createSensors(hw)

        self.assertEqual(s.getLineDirection(), 0)

    def test_line_direction_slight_left(self):
        """
        Čára je mezi středem a levým senzorem -> očekává se mírná korekce vlevo (+1).
        Surový stav: bit 3 (Middle) + bit 2 (Left) = 0b00001100 = 0x0C
        """
        hw = FakeI2C()
        hw.queue_read([0b00001100])
        s = createSensors(hw)

        self.assertEqual(s.getLineDirection(), 1)

    def test_line_direction_sharp_left(self):
        """
        Čára je zachycena pouze levým senzorem -> očekává se prudká korekce vlevo (+3).
        Surový stav: bit 2 (Left) = 0b00000100 = 0x04
        """
        hw = FakeI2C()
        hw.queue_read([0b00000100])
        s = createSensors(hw)

        self.assertEqual(s.getLineDirection(), 3)

    def test_line_direction_slight_right(self):
        """
        Čára je mezi středem a pravým senzorem -> očekává se mírná korekce vpravo (-1).
        Surový stav: bit 3 (Middle) + bit 4 (Right) = 0b00011000 = 0x18
        """
        hw = FakeI2C()
        hw.queue_read([0b00011000])
        s = createSensors(hw)

        self.assertEqual(s.getLineDirection(), -1)

    def test_line_direction_sharp_right(self):
        """
        Čára je zachycena pouze pravým senzorem -> očekává se prudká korekce vpravo (-3).
        Surový stav: bit 4 (Right) = 0b00010000 = 0x10
        """
        hw = FakeI2C()
        hw.queue_read([0b00010000])
        s = createSensors(hw)

        self.assertEqual(s.getLineDirection(), -3)

    def test_line_direction_out_of_line(self):
        """
        Žádný senzor nevidí čáru (bílá plocha) -> očekává se None.
        Surový stav: všechny bity čáry rovny 0 -> 0b00000000
        """
        hw = FakeI2C()
        hw.queue_read([0b00000000])
        s = createSensors(hw)

        self.assertIsNone(s.getLineDirection())

    def test_crossroads_detection(self):
        """
        Příčná čára / křižovatka: aktivní levý i pravý senzor současně.
        Ověříme:
        1. getTypeCrossRoads() vrací CrossRoadType.CROSS (3)
        2. getLineDirection() vrací None (není to běžná odchylka v pruhu)
        3. getSituationLine() vrací LineSituationEnum.CROSSROADS
        """
        hw = FakeI2C()
        # Všechny 3 senzory čáry aktivní (Left, Middle, Right) = 0b00011100
        hw.queue_read([0b00011100])
        s = createSensors(hw)

        self.assertEqual(s.getTypeCrossRoads(), CrossRoadType.CROSS)
        self.assertIsNone(s.getLineDirection())
        self.assertEqual(s.getSituationLine(), LineSituationEnum.CROSSROADS)

    def test_lost_line_debounce_timer(self):
        """
        Výukový test debounce časovače při ztrátě stopy:
        - Když robot sjede z čáry, nesmí okamžitě nahlásit chybu (None).
        - Po dobu 1000 ms stále hlásí LineSituationEnum.LINE (toleranční okno).
        - Teprve po překročení 1000 ms nahlásí None (definitivní ztráta).
        """
        hw = FakeI2C()
        # Nejprve jedeme po čáře (střední senzor)
        hw.queue_read([0b00001000])
        s = createSensors(hw, lostLineTimeoutMs=1000)
        self.assertEqual(s.getSituationLine(), LineSituationEnum.LINE)

        # Nyní simulujeme výpadek (surová 0 = žádný senzor nevidí čáru)
        hw.queue_read([0b00000000])
        # Vynutíme vypršení čtecí periody a aktualizaci
        s._periodRead._startTime = -100
        s.update()

        # V čase 500 ms detekujeme výpadek -> časovač se spustí v čase 500 ms
        fake_ticks.set_ticks_ms(500)
        self.assertEqual(s.getSituationLine(), LineSituationEnum.LINE)

        # V čase 1400 ms (uplynulo 900 ms ze zadaných 1000 ms) stále LINE
        fake_ticks.set_ticks_ms(1400)
        self.assertEqual(s.getSituationLine(), LineSituationEnum.LINE)

        # V čase 1501 ms (uplynulo 1001 ms od spuštění v 500 ms) vypršel timeout -> nahlásí None (ztracen)
        fake_ticks.set_ticks_ms(1501)
        self.assertIsNone(s.getSituationLine())

    def test_obstacle_sensors(self):
        """
        Ověření detekce čelních překážek:
        - ObstacleLeft  = bit 5 (0x20)
        - ObstacleRight = bit 6 (0x40)
        Překážkové senzory na PCF8574 nejsou invertovány XORem,
        takže aktivní překážka má na sběrnici bit roven 0.
        """
        hw = FakeI2C()
        # V klidu jsou vstupy pull-upovány na 1: 0b01100000 (oba 1 = volno)
        hw.queue_read([0b01100000])
        s = createSensors(hw)

        self.assertFalse(s.isObstacleLeft())
        self.assertFalse(s.isObstacleRight())
        self.assertFalse(s.isAnyObstacle())

        # Překážka vlevo: bit 5 spadne na 0 -> 0b01000000
        hw.queue_read([0b01000000])
        s._periodRead._startTime = -100
        s.update()

        self.assertTrue(s.isObstacleLeft())
        self.assertFalse(s.isObstacleRight())
        self.assertTrue(s.isAnyObstacle())


if __name__ == "__main__":
    unittest.main()
