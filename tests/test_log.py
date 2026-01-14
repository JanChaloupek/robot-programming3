import unittest
from code import Log, LogLevelEnum

class TestLog(unittest.TestCase):
    def test_log_info(self):
        log = Log(level=LogLevelEnum.INFO)
        log.info("hello")
        self.assertEqual(len(log._entries), 1)

    def test_log_debug_filtered(self):
        log = Log(level=LogLevelEnum.INFO)
        log.debug("debug")
        self.assertEqual(len(log._entries), 0)

    def test_flush_clears(self):
        log = Log(level=LogLevelEnum.DEBUG)
        log.info("x")
        log.flush()
        self.assertEqual(len(log._entries), 0)
