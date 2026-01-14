import unittest
from code import Wheels, PCA9633, I2C
from tests.fake_hw import FakeI2C

class FakeWheel:
    def __init__(self, should_fail=False):
        self.stopped = False
        self.should_fail = should_fail

    def stop(self):
        if self.should_fail:
            raise RuntimeError("Wheel failure")
        self.stopped = True

class TestEmergencyShutdown(unittest.TestCase):
    def test_shutdown_success(self):
        hw = FakeI2C()
        wheels = Wheels(PCA9633(I2C(hw)))

        # Nahraď skutečná kola fake objekty
        wheels._wheels = {
            "left": FakeWheel(),
            "right": FakeWheel()
        }

        wheels.emergencyShutdown()

        self.assertTrue(wheels._wheels["left"].stopped)
        self.assertTrue(wheels._wheels["right"].stopped)

    def test_shutdown_with_failure(self):
        hw = FakeI2C()
        wheels = Wheels(PCA9633(I2C(hw)))

        wheels._wheels = {
            "left": FakeWheel(),
            "right": FakeWheel(should_fail=True)
        }

        with self.assertRaises(RuntimeError):
            wheels.emergencyShutdown()
