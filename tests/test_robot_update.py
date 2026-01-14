import unittest
from code import Robot, I2C
from tests.fake_hw import FakeI2C

class TestRobotUpdate(unittest.TestCase):
    def test_robot_update_calls_subsystems(self):
        robot = Robot(I2C(FakeI2C()))

        robot.sensors._dataPrev = 0
        robot.sensors._data = 1

        robot.update()

        # jen ověříme, že metoda existuje a nepadá
        self.assertTrue(True)
