"""
log.py – jednoduchý logovací systém s časovými značkami.

Poskytuje:
- různé úrovně logování (ERROR, WARNING, INFO, DEBUG),
- ukládání logů do paměti,
- tisk logů s časovými značkami,
- možnost filtrování podle úrovně.

Vhodné pro libovolné projekty v CircuitPythonu.
"""

from adafruit_ticks import ticks_ms


class LogLevel:
    """Reprezentuje jednu úroveň logování."""

    def __init__(self, name, value):
        self.name = name
        self.value = value


class LogLevelEnum:
    """Enum-like kolekce úrovní logování."""

    ERROR = LogLevel("ERROR", 1)
    WARNING = LogLevel("WARNING", 2)
    INFO = LogLevel("INFO", 3)
    DEBUG = LogLevel("DEBUG", 4)


class Log:
    """
    Jednoduchý logovací systém s časovými značkami.

    Logy se ukládají do interního bufferu a lze je kdykoliv vytisknout
    pomocí metody flush().
    """

    def __init__(self, level=LogLevelEnum.INFO):
        self._initTime = ticks_ms()
        self._level = level
        self._entries = []

    def _log(self, level, text):
        """Zapíše log do bufferu, pokud úroveň odpovídá nastavení."""
        if self._level.value >= level.value:
            dif = ticks_ms() - self._initTime
            self._entries.append((dif, level.name, text))

    def flush(self, max_line=None):
        """
        Vytiskne logy a smaže je.

        Args:
            max_line (int|None): Maximální počet vypsaných řádků.
        """
        count = 0
        while self._entries:
            dif, name, text = self._entries.pop(0)
            print(f"[{dif:6d} ms|{name:7}] {text}")
            count += 1
            if max_line is not None and count >= max_line:
                break

    def debug(self, text):
        """Zapíše ladicí zprávu."""
        self._log(LogLevelEnum.DEBUG, text)

    def info(self, text):
        """Zapíše informativní zprávu."""
        self._log(LogLevelEnum.INFO, text)

    def warning(self, text):
        """Zapíše varování."""
        self._log(LogLevelEnum.WARNING, text)

    def error(self, text):
        """Zapíše chybovou zprávu."""
        self._log(LogLevelEnum.ERROR, text)

    def exception(self, e):
        """Zapíše výjimku jako chybu."""
        self.error("Exception: " + str(e))


log = Log(level=LogLevelEnum.DEBUG)
