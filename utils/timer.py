"""
timer.py – jednoduchý jednorázový časovač.

Poskytuje:
- měření uplynulého času,
- detekci timeoutu,
- restart a zastavení časovače,
- moderní API: ready(), restart(), elapsed().

API:
- is_timeout(test_time_ms=None, timeout_ms=None)  -> čistý test bez vedlejších efektů
- isTimeout(...)                                   -> alias pro zpětnou kompatibilitu
- ready()                                          -> pohodlný test (Timer: nerestartuje)
- restart(), startTimer(), stopTimer(), elapsed(), getTimeDiff()

Vhodné pro libovolné projekty v CircuitPythonu.

"""

from __future__ import annotations

# Pokusíme se získat informaci o TYPE_CHECKING bez přímého "from typing import ..."
# protože některé CircuitPython buildy modul typing vůbec nemají.
try:
    import typing as _typing  # type: ignore
    TYPE_CHECKING = getattr(_typing, "TYPE_CHECKING", False)
except Exception:
    TYPE_CHECKING = False

# Importy pro statickou analýzu (provedou se jen pokud TYPE_CHECKING je True v editoru).
if TYPE_CHECKING:
    from typing import Optional  # type: ignore

from adafruit_ticks import ticks_ms, ticks_diff

class Timer:
    """
    Jednorázový časovač.

    Konstrukce:
        Timer(timeout_ms=None, startTimer=True)

    Chování:
        - is_timeout(...) provádí čistý test (bez změny stavu).
        - ready() je pohodlná metoda: u Timer vrací True pokud timeout vypršel (nerestartuje).
    """

    def __init__(self, timeout_ms: "Optional[int]" = None, startTimer: bool = True) -> None:
        self.timeout_ms = timeout_ms
        self._startTime = None
        if startTimer:
            self.startTimer()

    def startTimer(self, start_time_ms: "Optional[int]" = None, timeout_ms: "Optional[int]" = None) -> None:
        """
        Spustí časovač.

        Args:
            start_time_ms: počáteční čas v ms (pokud None, použije se aktuální čas)
            timeout_ms: nový timeout v ms (pokud None, použije se existující)
        """
        if timeout_ms is not None:
            self.timeout_ms = timeout_ms
        self._startTime = ticks_ms() if start_time_ms is None else start_time_ms

    def restart(self) -> None:
        """Restartuje časovač od aktuálního času."""
        self._startTime = ticks_ms()

    def stopTimer(self) -> None:
        """Zastaví časovač (nastaví jako nespustený)."""
        self._startTime = None

    def isStarted(self) -> bool:
        """Vrací True, pokud je časovač aktivní."""
        return self._startTime is not None

    def elapsed(self) -> int:
        """Vrátí uplynulý čas od spuštění v ms. Pokud není spuštěn, vrací 0."""
        if self._startTime is None:
            return 0
        return ticks_diff(ticks_ms(), self._startTime)

    def is_timeout(self, test_time_ms: "Optional[int]" = None, timeout_ms: "Optional[int]" = None) -> bool:
        """
        Čistý test, zda timeout vypršel. NEZMĚNÍ stav časovače.

        Args:
            test_time_ms: čas, vůči kterému se testuje (pokud None, použije se aktuální čas)
            timeout_ms: timeout v ms (pokud None, použije se self.timeout_ms)

        Returns:
            True pokud timeout vypršel, jinak False.
        """
        if self._startTime is None:
            return False

        if timeout_ms is None:
            timeout_ms = self.timeout_ms
        if timeout_ms is None:
            return False

        if test_time_ms is None:
            test_time_ms = ticks_ms()

        return ticks_diff(test_time_ms, self._startTime) >= timeout_ms

    # alias pro zpětnou kompatibilitu
    isTimeout = is_timeout

    def ready(self) -> bool:
        """
        Pohodlný test používaný v hlavní smyčce.

        U Timer: vrací True pokud timeout vypršel; NERESTARTUJE časovač.
        (Pro periodické chování použij Period.ready().)
        """
        return self.is_timeout()

    def getTimeDiff(self, test_time_ms: "Optional[int]" = None) -> int:
        """
        Vrátí rozdíl času od spuštění (v ms) vůči test_time_ms nebo aktuálnímu času.
        Pokud časovač není spuštěn, vrací 0.
        """
        if self._startTime is None:
            return 0
        if test_time_ms is None:
            test_time_ms = ticks_ms()
        return ticks_diff(test_time_ms, self._startTime)
