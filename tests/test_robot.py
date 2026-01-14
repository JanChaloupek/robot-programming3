import unittest
from code import Robot, I2C
from tests.fake_hw import FakeI2C

class TestRobot(unittest.TestCase):
    def test_robot_init(self):
        r = Robot(I2C(FakeI2C()))
        self.assertIsNotNone(r.sensors)
        self.assertIsNotNone(r.wheels)
