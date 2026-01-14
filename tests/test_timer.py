import unittest
from code import Timer, Period

class TestTimer(unittest.TestCase):
    def test_timeout(self):
        t = Timer(timeout_ms=100)
        t._startTime = 0
        self.assertTrue(t.isTimeout(test_time_ms=200))

    def test_not_started(self):
        t = Timer(startTimer=False)
        self.assertFalse(t.isTimeout())

class TestPeriod(unittest.TestCase):
    def test_period_resets(self):
        p = Period(timeout_ms=100)
        p._startTime = 0
        self.assertTrue(p.isTime(test_time_ms=200))
        self.assertNotEqual(p._startTime, 0)
