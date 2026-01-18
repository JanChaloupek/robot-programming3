"""
log.py – jednoduchý logovací systém s časovými značkami.

Použití:
    from utils.log import log, LogLevelEnum

    log.info("Start programu")
    log.debug("Detailní zpráva")
"""

from adafruit_ticks import ticks_ms


class LogLevel:
    """Reprezentuje jednu úroveň logování."""
    def __init__(self, name: str, value: int) -> None:
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

    Atributy:
        level (LogLevel): Minimální úroveň logování.
        _initTime (int): Čas inicializace loggeru v ms.
    """

    def __init__(self, level: LogLevel = LogLevelEnum.INFO) -> None:
        self._initTime: int = ticks_ms()
        self._level: LogLevel = level
        self._entries = []

    def _log(self, level: LogLevel, text: str) -> None:
        """Interní metoda pro zápis logu."""
        if self._level.value >= level.value:
            difTime_ms = ticks_ms() - self._initTime
            self._entries.append((difTime_ms, level.name, text))

    def flush(self, max_line: int = None) -> None:
        """Vytiskne logy a smaže je."""
        count = 0
        while self._entries:
            difTime_ms, level_name, text = self._entries.pop(0)
            print(f"[{difTime_ms:6d} ms|{level_name:7}] {text}")
            count += 1
            if max_line is not None and count >= max_line:
                break

    def debug(self, text: str) -> None:
        """Zapíše ladicí zprávu."""
        self._log(LogLevelEnum.DEBUG, text)

    def info(self, text: str) -> None:
        """Zapíše informativní zprávu."""
        self._log(LogLevelEnum.INFO, text)

    def warning(self, text: str) -> None:
        """Zapíše varování."""
        self._log(LogLevelEnum.WARNING, text)

    def error(self, text: str) -> None:
        """Zapíše chybovou zprávu."""
        self._log(LogLevelEnum.ERROR, text)

    def exception(self, e: BaseException) -> None:
        """Zapíše výjimku jako chybu."""
        self.error(f"Exception: {str(e)}")


log = Log(level=LogLevelEnum.DEBUG)
