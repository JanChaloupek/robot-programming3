"""
fake_time.py – neblokující náhrada modulu time pro unit testy

Účel:
- studenti mohou používat time.sleep() bez blokování testů
- time.time() vrací deterministický čas
- čas je řízen přes adafruit_ticks (set_ticks_ms, advance_ticks)
"""

import adafruit_ticks as ticks


def time() -> float:
    """
    Vrací simulovaný čas v sekundách.
    """
    return ticks.ticks_ms() / 1000.0


def sleep(seconds: float) -> None:
    """
    Neblokující sleep – pouze posune simulovaný čas.
    """
    ms = int(seconds * 1000)
    ticks.advance_ticks(ms)


def sleep_ms(ms: int) -> None:
    """
    MicroPython kompatibilní varianta.
    """
    ticks.advance_ticks(int(ms))
