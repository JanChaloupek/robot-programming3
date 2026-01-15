import unittest
from code import Robot, I2C
from picoed import FakeI2C


class TestRobot(unittest.TestCase):
    """
    Testy základní inicializace třídy Robot.

    Tento test ověřuje, že po vytvoření instance Robot:
        - jsou inicializovány senzory
        - jsou inicializována kola (Wheels)
        - konstruktor nevyvolá žádnou výjimku
        - hardware lze bezpečně simulovat pomocí FakeI2C

    Test slouží jako sanity‑check správné struktury objektu Robot.
    """

    def test_robot_init(self):
        """
        Ověříme, že Robot po inicializaci obsahuje
        platné objekty sensors a wheels.
        """

        r = Robot(I2C(FakeI2C()))

        self.assertIsNotNone(r.sensors)
        self.assertIsNotNone(r.wheels)
