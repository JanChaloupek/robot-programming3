import unittest
from code import Robot, I2C
from tests.fake_hw import FakeI2C

class TestRobotShutdown(unittest.TestCase):
    def test_robot_shutdown(self):
        robot = Robot(I2C(FakeI2C()))
        # jen ověříme, že metoda existuje a nepadá
        robot.emergencyShutdown()
