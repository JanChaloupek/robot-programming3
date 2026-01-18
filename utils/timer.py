"""
timer.py – jednorázový časovač pro JoyCar.

Použití:
    from utils.timer import Timer

    t = Timer(timeout_ms=1000)
    if t.isTimeout():
        ...
"""

from adafruit_ticks import ticks_ms, ticks_diff


class Timer:
    """
    Jednoduchý jednorázový časovač.

    Atributy:
        timeout_ms (int): Nastavený timeout v milisekundách.
        _startTime (int|None): Čas spuštění časovače.
    """

    def __init__(self, timeout_ms: int = None, startTimer: bool = True) -> None:
        self.timeout_ms = timeout_ms
        if startTimer:
            self.startTimer()
        else:
            self.stopTimer()

    def startTimer(self, start_time_ms: int = None, timeout_ms: int = None) -> None:
        """Spustí časovač."""
        if timeout_ms is not None:
            self.timeout_ms = timeout_ms
        self._startTime = self._getTime(start_time_ms)

    def stopTimer(self) -> None:
        """Zastaví časovač."""
        self._startTime = None

    def isStarted(self) -> bool:
        """Vrací True, pokud je časovač aktivní."""
        return self._startTime is not None

    def _getTime(self, time_ms: int) -> int:
        """Vrátí zadaný čas nebo aktuální čas v ms."""
        if time_ms is None:
            time_ms = ticks_ms()
        return time_ms

    def _getTimeout(self, timeout_ms: int = None) -> int:
        """Vrátí timeout – buď zadaný, nebo výchozí nebo nulový."""
        if timeout_ms is None:
            timeout_ms = self.timeout_ms
        if timeout_ms is None:
            timeout_ms = 0
        return timeout_ms

    def getTimeDiff(self, test_time_ms: int = None) -> int:
        """Vrátí rozdíl času od spuštění."""
        self.lastTimeDiff = ticks_diff(self._getTime(test_time_ms), self._startTime)
        return self.lastTimeDiff

    def isTimeout(self, test_time_ms: int = None, timeout_ms: int = None) -> bool:
        """Vrátí True, pokud vypršel timeout."""
        if not self.isStarted():
            return False
        return self.getTimeDiff(test_time_ms) >= self._getTimeout(timeout_ms)
