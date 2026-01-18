"""
period.py – periodický časovač pro JoyCar.

Použití:
    from utils.period import Period

    p = Period(timeout_ms=500)
    if p.isTime():
        ...
"""

from utils.timer import Timer


class Period(Timer):
    """Periodický časovač – po timeoutu se automaticky restartuje."""

    def isTime(self, test_time_ms: int = None, timeout_ms: int = None) -> bool:
        """Vrátí True, pokud nastal čas události, a restartuje časovač."""
        time_ms = self._getTime(test_time_ms)
        ret = self.isTimeout(time_ms, timeout_ms)
        if ret:
            self.startTimer(time_ms)
        return ret
