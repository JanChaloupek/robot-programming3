import unittest
from utils.log import Log, LogLevelEnum


class TestLog(unittest.TestCase):
    """
    Testy základní funkcionality třídy Log.

    Ověřujeme, že:
        - zprávy s úrovní INFO se ukládají, pokud je log nastaven na INFO
        - zprávy s úrovní DEBUG se filtrují, pokud je log nastaven na INFO
        - flush() správně vymaže všechny uložené záznamy

    Testy slouží jako sanity‑check správného filtrování a správy logovacích záznamů.
    """

    def test_log_info(self):
        """
        Ověříme, že zpráva s úrovní INFO se uloží,
        pokud je log nastaven na úroveň INFO.
        """
        log = Log(level=LogLevelEnum.INFO)
        log.info("hello")
        self.assertEqual(len(log._entries), 1)

    def test_log_debug_filtered(self):
        """
        Ověříme, že zpráva s úrovní DEBUG se neuloží,
        pokud je log nastaven na úroveň INFO.
        """
        log = Log(level=LogLevelEnum.INFO)
        log.debug("debug")
        self.assertEqual(len(log._entries), 0)

    def test_flush_clears(self):
        """
        Ověříme, že flush() vymaže všechny uložené záznamy.
        """
        log = Log(level=LogLevelEnum.DEBUG)
        log.info("x")
        log.flush()
        self.assertEqual(len(log._entries), 0)
