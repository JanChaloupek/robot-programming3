"""
time.py – společný stub pro VS Code a fake hardware pro testy.

Tento modul nahrazuje standardní Python modul `time` při unit testech.
Je navržen tak, aby:

- time.time() vracelo deterministický čas
- time.sleep() NEblokovalo testy
- čas byl řízen přes adafruit_ticks (set_ticks_ms, advance_ticks)
- studenti mohli používat známé API (time.sleep, time.sleep_ms)
- testy byly rychlé, deterministické a bez čekání

Reálný modul `time` používá systémové hodiny a blokující sleep().
Tento fake modul je určený pouze pro výuku a testování na PC.
"""

import adafruit_ticks as ticks


def time() -> float:
    """
    Vrací simulovaný čas v sekundách.

    V reálném Pythonu:
        time.time() vrací POSIX čas (unix timestamp).

    V této fake verzi:
        - vrací ticks_ms() / 1000
        - čas je řízen testy (set_ticks_ms, advance_ticks)
        - nikdy se neaktualizuje automaticky
    """
    return ticks.ticks_ms() / 1000.0


def sleep(seconds: float) -> None:
    """
    Neblokující sleep – pouze posune simulovaný čas.

    Parametry:
        seconds – počet sekund, o které se má čas posunout

    V reálném Pythonu:
        time.sleep() blokuje vlákno.

    V této fake verzi:
        - pouze posune simulovaný čas
        - testy běží okamžitě
    """
    ms = int(seconds * 1000)
    ticks.advance_ticks(ms)


def sleep_ms(ms: int) -> None:
    """
    MicroPython kompatibilní varianta sleepu v milisekundách.

    Parametry:
        ms – počet milisekund, o které se má čas posunout
    """
    ticks.advance_ticks(int(ms))
