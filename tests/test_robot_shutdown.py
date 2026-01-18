import unittest
from lib_vsc_only.busio import I2C as FakeI2C
from tests.create import createRobot


class TestRobotShutdown(unittest.TestCase):
    """
    Testy nouzového vypnutí robota.

    Tento test ověřuje, že metoda emergencyShutdown():
        - existuje
        - lze ji zavolat bez výjimky
        - nevyžaduje žádné parametry
        - je bezpečná i při prázdném nebo neaktivním hardware

    Test je navržen jako sanity‑check:
        - neověřuje konkrétní chování motorů
        - neověřuje logiku reverzu
        - pouze zajišťuje, že metoda je implementována a stabilní
    """

    def test_robot_shutdown(self):
        """
        Ověříme, že emergencyShutdown() lze zavolat
        a metoda nespadne ani v základní konfiguraci robota.
        """

        robot = createRobot(FakeI2C())

        # jen ověříme, že metoda existuje a nepadá
        robot.emergencyShutdown()
