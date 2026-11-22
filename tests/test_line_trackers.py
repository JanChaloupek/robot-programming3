"""
test_line_trackers.py – Unit testy pro přepínání 2 až 6 senzorů čáry.
"""

import unittest
from busio import I2C as FakeI2C
from tests.create import createSensors
from joycar.sensors import Sensors, CrossRoadType
from joycar.line_trackers import (
    LineTracker2, LineTracker3, LineTracker4, LineTracker5, LineTracker6, createLineTracker
)


class TestLineTrackers(unittest.TestCase):
    """Testuje strategie vyhodnocování čáry pro různé počty senzorů."""

    def test_create_line_tracker(self):
        self.assertIsInstance(createLineTracker(2), LineTracker2)
        self.assertIsInstance(createLineTracker(3), LineTracker3)
        self.assertIsInstance(createLineTracker(4), LineTracker4)
        self.assertIsInstance(createLineTracker(5), LineTracker5)
        self.assertIsInstance(createLineTracker(6), LineTracker6)
        with self.assertRaises(ValueError):
            createLineTracker(7)

    def test_line_tracker_2_sensors(self):
        hw = FakeI2C()
        s = createSensors(hw, lineSensorCount=2)
        self.assertEqual(s.lineSensorCount, 2)

        # Čára mezi senzory (oba bílá = surové čtení 0x00) -> směr 0
        hw.queue_read([0x00])
        s.updateSensorData()
        self.assertEqual(s.getLineDirection(), 0)

        # Čára pod levým senzorem (0x04) -> směr +2
        hw.queue_read([0x04])
        s.updateSensorData()
        self.assertEqual(s.getLineDirection(), 2)

        # Čára pod pravým senzorem (0x10) -> směr -2
        hw.queue_read([0x10])
        s.updateSensorData()
        self.assertEqual(s.getLineDirection(), -2)

        # Oba senzory na čáře (0x14) -> křižovatka
        hw.queue_read([0x14])
        s.updateSensorData()
        self.assertEqual(s.getTypeCrossRoads(), CrossRoadType.CROSS)

    def test_switch_sensor_count_dynamically(self):
        hw = FakeI2C()
        s = createSensors(hw, lineSensorCount=3)
        self.assertEqual(s.lineSensorCount, 3)

        s.setLineSensorCount(5)
        self.assertEqual(s.lineSensorCount, 5)

        # FarLeft (0x01) aktivní -> směr +5
        hw.queue_read([0x01])
        s.updateSensorData()
        self.assertEqual(s.getLineDirection(), 5)


if __name__ == "__main__":
    unittest.main()
