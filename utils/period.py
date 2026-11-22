"""
period.py – periodický časovač.

Period funguje jako Timer, ale po timeoutu se automaticky restartuje.
Vhodné pro libovolné projekty v CircuitPythonu.
"""

from utils import Timer


class Period(Timer):
    """
    Periodický časovač – po timeoutu se automaticky restartuje.

    Chování:
        - ready() nebo isTime() vrací True pokud timeout vypršel a zároveň restartuje časovač.
        - is_timeout(...) zůstává čistým testem bez efektů (zděděno z Timer).
    """

    def isTime(self, test_time_ms=None, timeout_ms=None) -> bool:
        """
        Vrátí True, pokud nastal čas události, a restartuje časovač.
        Kompatibilní s MicroPython i CircuitPython verzí.
        """
        if self.is_timeout(test_time_ms, timeout_ms):
            self.restart()
            return True
        return False

    # Alias pro moderní PEP8 konvenci
    is_time = isTime

    def ready(self) -> bool:
        """
        Vrátí True, pokud nastal čas události, a restartuje časovač.

        Použití:
            p = Period(timeout_ms=500)
            if p.ready():
                # vykonej periodickou akci
        """
        return self.isTime()
