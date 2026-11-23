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

    def test_line_tracker_3_sensors(self):
        """Ověří vyhodnocování pro tovární 3 senzory JoyCar."""
        hw = FakeI2C()
        s = createSensors(hw, lineSensorCount=3)

        # Střední senzor (0x08) -> jedeme rovně (směr 0)
        hw.queue_read([0x08])
        s.updateSensorData()
        self.assertEqual(s.getLineDirection(), 0)

        # Střední + levý (0x0C) -> mírně vlevo (směr +1)
        hw.queue_read([0x0C])
        s.updateSensorData()
        self.assertEqual(s.getLineDirection(), 1)
        self.assertEqual(s.getTypeCrossRoads(), CrossRoadType.LEFT)

        # Pouze levý (0x04) -> výrazně vlevo (směr +3)
        hw.queue_read([0x04])
        s.updateSensorData()
        self.assertEqual(s.getLineDirection(), 3)

        # Střední + pravý (0x18) -> mírně vpravo (směr -1)
        hw.queue_read([0x18])
        s.updateSensorData()
        self.assertEqual(s.getLineDirection(), -1)
        self.assertEqual(s.getTypeCrossRoads(), CrossRoadType.RIGHT)

        # Pouze pravý (0x10) -> výrazně vpravo (směr -3)
        hw.queue_read([0x10])
        s.updateSensorData()
        self.assertEqual(s.getLineDirection(), -3)

        # Levý + pravý (0x14) nebo všechny (0x1C) -> křižovatka CROSS
        hw.queue_read([0x14])
        s.updateSensorData()
        self.assertIsNone(s.getLineDirection())
        self.assertEqual(s.getTypeCrossRoads(), CrossRoadType.CROSS)

    def test_line_tracker_4_sensors(self):
        """Ověří vyhodnocování pro 4 senzory (2 středové + 2 vnější)."""
        hw = FakeI2C()
        s = createSensors(hw, lineSensorCount=4)

        # Oba vnitřní senzory (0x08 | 0x80 = 0x88) -> střed (0)
        hw.queue_read([0x88])
        s.updateSensorData()
        self.assertEqual(s.getLineDirection(), 0)

        # Vnitřní levý (0x08) -> mírně vlevo (+1)
        hw.queue_read([0x08])
        s.updateSensorData()
        self.assertEqual(s.getLineDirection(), 1)

        # Vnější levý + vnitřní levý (0x0C) -> středně vlevo (+2), křižovatka LEFT
        hw.queue_read([0x0C])
        s.updateSensorData()
        self.assertEqual(s.getLineDirection(), 2)
        self.assertEqual(s.getTypeCrossRoads(), CrossRoadType.LEFT)

        # Pouze vnější levý (0x04) -> více vlevo (+3)
        hw.queue_read([0x04])
        s.updateSensorData()
        self.assertEqual(s.getLineDirection(), 3)

        # Vnější pravý + vnitřní pravý (0x10 | 0x80 = 0x90) -> křižovatka RIGHT
        hw.queue_read([0x90])
        s.updateSensorData()
        self.assertEqual(s.getLineDirection(), -2)
        self.assertEqual(s.getTypeCrossRoads(), CrossRoadType.RIGHT)

        # Levý + pravý vnější (0x14) -> křižovatka CROSS
        hw.queue_read([0x14])
        s.updateSensorData()
        self.assertIsNone(s.getLineDirection())
        self.assertEqual(s.getTypeCrossRoads(), CrossRoadType.CROSS)

    def test_line_tracker_5_sensors(self):
        """Ověří vyhodnocování pro 5 senzorů (3 středové + 2 předsazené krajní)."""
        hw = FakeI2C()
        s = createSensors(hw, lineSensorCount=5)

        # Předsazený FarLeft (0x01) -> směr +5, křižovatka LEFT
        hw.queue_read([0x01])
        s.updateSensorData()
        self.assertEqual(s.getLineDirection(), 5)
        self.assertEqual(s.getTypeCrossRoads(), CrossRoadType.LEFT)

        # Předsazený FarRight (0x02) -> směr -5, křižovatka RIGHT
        hw.queue_read([0x02])
        s.updateSensorData()
        self.assertEqual(s.getLineDirection(), -5)
        self.assertEqual(s.getTypeCrossRoads(), CrossRoadType.RIGHT)

        # Oba předsazené současně (0x03) -> křižovatka CROSS
        hw.queue_read([0x03])
        s.updateSensorData()
        self.assertIsNone(s.getLineDirection())
        self.assertEqual(s.getTypeCrossRoads(), CrossRoadType.CROSS)

    def test_line_tracker_6_sensors(self):
        """Ověří vyhodnocování pro 6 senzorů (plná výbava z 2-SW_GIT s 9 zónami)."""
        hw = FakeI2C()
        s = createSensors(hw, lineSensorCount=6)

        # Extrémní levé vyosení FarLeft (0x01) -> směr +6
        hw.queue_read([0x01])
        s.updateSensorData()
        self.assertEqual(s.getLineDirection(), 6)

        # Extrémní pravé vyosení FarRight (0x02) -> směr -6
        hw.queue_read([0x02])
        s.updateSensorData()
        self.assertEqual(s.getLineDirection(), -6)

        # Střední dvojice (0x88) -> směr 0
        hw.queue_read([0x88])
        s.updateSensorData()
        self.assertEqual(s.getLineDirection(), 0)

        # Oba krajní aktivní (0x03) -> křižovatka CROSS
        hw.queue_read([0x03])
        s.updateSensorData()
        self.assertIsNone(s.getLineDirection())
        self.assertEqual(s.getTypeCrossRoads(), CrossRoadType.CROSS)


if __name__ == "__main__":
    unittest.main()
