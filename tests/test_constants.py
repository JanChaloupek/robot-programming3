"""
test_constants.py – Unit testy pro matematické konstanty a enumeraci směrů.
"""

import unittest
import math
from utils.constants import PI, TWO_PI, HALF_PI
from joycar.direction import DirectionEnum


class TestConstantsAndEnums(unittest.TestCase):
    """Testovací sada pro konstanty a základní datové typy."""

    def test_math_constants(self):
        """Ověří přesnost matematických konstant."""
        self.assertAlmostEqual(PI, math.pi)
        self.assertAlmostEqual(TWO_PI, 2 * math.pi)
        self.assertAlmostEqual(HALF_PI, math.pi / 2)

    def test_direction_enum_values(self):
        """Ověří textové hodnoty DirectionEnum."""
        self.assertEqual(DirectionEnum.LEFT, "left")
        self.assertEqual(DirectionEnum.RIGHT, "right")
        self.assertEqual(DirectionEnum.FORWARD, "forward")
        self.assertEqual(DirectionEnum.BACKWARD, "backward")


if __name__ == "__main__":
    unittest.main()
