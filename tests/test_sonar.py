"""
test_sonar.py – Unit a integrační testy pro ultrazvukový dálkoměr Sonar (v metrech).
"""

import unittest
from joycar.sonar import Sonar
from joycar import JoyCarRobot, I2C
from busio import I2C as FakeI2C
import _fake.adafruit_ticks as fake_ticks


class TestSonar(unittest.TestCase):
    """Testovací sada pro ultrazvukový dálkoměr Sonar v základních jednotkách SI (metry)."""

    def setUp(self):
        fake_ticks.set_ticks_ms(0)

    def test_sonar_init_disabled(self):
        """Ověří, že ve výchozím stavu (enabled=False) sonar neměří a vrací None."""
        sonar = Sonar(enabled=False)
        self.assertFalse(sonar.is_enabled)
        self.assertIsNone(sonar.distance)

        # Volání update() při vypnutém stavu nic neprovede
        sonar.update()
        self.assertIsNone(sonar.distance)

    def test_sonar_enable_and_disable(self):
        """Ověří bezpečné zapínání a vypínání měření za běhu."""
        sonar = Sonar(enabled=False)
        self.assertFalse(sonar.is_enabled)

        sonar.enable()
        self.assertTrue(sonar.is_enabled)

        # Nastavíme mock hodnotu 0.25 m
        sonar.set_mock_distance(0.25)
        sonar.measure()
        self.assertEqual(sonar.distance, 0.25)

        # Vypnutí sonaru resetuje měření
        sonar.disable()
        self.assertFalse(sonar.is_enabled)
        self.assertIsNone(sonar.distance)

    def test_distance_calculation_in_meters(self):
        """Ověří přepočet doby letu pulzu na metry (1166 us odpovídá 0.20 m)."""
        sonar = Sonar(enabled=True)
        sonar.set_mock_distance(0.20)
        sonar.measure()

        # Vzdálenost musí být přesně v metrech
        self.assertEqual(sonar.distance, 0.20)

    def test_moving_average_smoothing_filter(self):
        """Ověří vyhlazovací filtr klouzavého průměru (odstranění falešných zámitů)."""
        sonar = Sonar(enabled=True)

        # Série stabilních měření: 0.20 m
        sonar.set_mock_distance(0.20)
        sonar.measure()
        sonar.measure()
        sonar.measure()
        self.assertEqual(sonar.distance, 0.20)

        # Přijde jednorázový falešný odraz: 0.80 m (šum)
        sonar.set_mock_distance(0.80)
        sonar.measure()

        # Hodnota se skokově nezměnila na 0.80 m, filtr ji vyhladil: (0.20 + 0.20 + 0.80) / 3 = 0.40 m
        self.assertEqual(sonar.distance, 0.40)

        # Následující měření jsou opět stabilní 0.20 m
        sonar.set_mock_distance(0.20)
        sonar.measure()
        self.assertEqual(sonar.distance, 0.40)

        sonar.measure()
        self.assertEqual(sonar.distance, 0.40)

        # Po 3 stabilních vzorcích je šum 0.80 m zcela vytlačen z okna filtru
        sonar.measure()
        self.assertEqual(sonar.distance, 0.20)

    def test_out_of_range_and_timeout(self):
        """Ověří, že překážka mimo dosah (timeout / volný prostor) vrací None."""
        sonar = Sonar(enabled=True)

        # Simulujeme volný prostor (timeout měření)
        sonar.set_mock_distance(None)
        sonar.measure()
        sonar.measure()
        sonar.measure()

        self.assertIsNone(sonar.distance)

    def test_nonblocking_superloop_period(self):
        """Ověří, že měření probíhá neblokujícím způsobem přes Period."""
        sonar = Sonar(timeout_ms=60, enabled=True)
        sonar.set_mock_distance(0.30)

        # V čase 0 ms proběhne první měření
        sonar.update()
        self.assertEqual(sonar.distance, 0.30)

        # Změníme simulovanou vzdálenost na 0.10 m, ale čas posuneme jen o 30 ms (< 60 ms)
        sonar.set_mock_distance(0.10)
        fake_ticks.set_ticks_ms(30)
        sonar.update()

        # Perioda ještě nevypršela -> zůstává původní hodnota 0.30 m
        self.assertEqual(sonar.distance, 0.30)

        # V čase 65 ms perioda vypršela -> proběhne nové měření
        fake_ticks.set_ticks_ms(65)
        sonar.update()
        # Klouzavý průměr z 0.30 a 0.10 m = 0.20 m
        self.assertEqual(sonar.distance, 0.20)

    def test_is_obstacle_near(self):
        """Ověří metodu is_obstacle_near(threshold_m)."""
        sonar = Sonar(enabled=True)

        # Překážka na 0.15 m
        sonar.set_mock_distance(0.15)
        sonar.measure()
        self.assertTrue(sonar.is_obstacle_near(threshold_m=0.20))
        self.assertFalse(sonar.is_obstacle_near(threshold_m=0.10))

        # Volný prostor
        sonar.set_mock_distance(None)
        sonar.measure()
        sonar.measure()
        sonar.measure()
        self.assertFalse(sonar.is_obstacle_near(threshold_m=0.20))

    def test_robot_sonar_integration_and_stop_ahead(self):
        """Ověří začlenění sonaru do JoyCarRobot a automatické zastavení před překážkou."""
        hw = FakeI2C()
        robot = JoyCarRobot(I2C(hw), sonar_enabled=True)

        # Zkontrolujeme propojení subsystému
        self.assertTrue(robot.sonar.is_enabled)
        robot.sonar.set_mock_distance(0.15)
        robot.update()

        self.assertEqual(robot.getObstacleDistance(), 0.15)
        self.assertTrue(robot.isObstacleAhead(distance_m=0.20))
        self.assertFalse(robot.isObstacleAhead(distance_m=0.10))

        # Test autonomní jízdy: překážka na 0.15 m, bezpečnostní limit 0.20 m -> robot zastaví (rychlost 0.0)
        robot.rideLine(baseSpeed=0.25, minObstacleDistance=0.20)
        self.assertEqual(robot._linearSpeed, 0.0)


if __name__ == "__main__":
    unittest.main()
