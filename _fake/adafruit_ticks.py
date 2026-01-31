# _fake/adafruit_ticks.py

"""
Fake implementace modulu adafruit_ticks pro testy a vývoj na PC.

Simuluje monotónní časovač CircuitPythonu:
- ticks_ms() vrací řízený simulovaný čas
- ticks_add() a ticks_diff() fungují stejně jako v MicroPythonu
- čas se neposouvá automaticky, testy jej řídí ručně
"""

# Konstanty převzaté z MicroPythonu
_TICKS_PERIOD = 1 << 29
_TICKS_MAX = _TICKS_PERIOD - 1
_TICKS_HALFPERIOD = _TICKS_PERIOD // 2

# Interní simulovaný čas (v milisekundách)
_fake_ticks = 0


def ticks_ms() -> int:
    """Vrací aktuální simulovaný čas v milisekundách."""
    return _fake_ticks


def ticks_add(ticks: int, delta: int) -> int:
    """Vrací ticks + delta s bezpečným přetečením."""
    return (ticks + delta) % _TICKS_PERIOD


def ticks_diff(ticks1: int, ticks2: int) -> int:
    """Vrací rozdíl dvou tick hodnot s ošetřením přetečení."""
    diff = (ticks1 - ticks2) & _TICKS_MAX
    diff = ((diff + _TICKS_HALFPERIOD) & _TICKS_MAX) - _TICKS_HALFPERIOD
    return diff


def ticks_less(ticks1: int, ticks2: int) -> bool:
    """Vrací True, pokud ticks1 je dříve než ticks2."""
    return ticks_diff(ticks1, ticks2) < 0


# ---------------------------------------------------------
# FakeHW rozšíření – pouze pro testy
# ---------------------------------------------------------

def set_ticks_ms(value: int) -> None:
    """Nastaví simulovaný čas v milisekundách."""
    global _fake_ticks
    _fake_ticks = int(value)


def advance_ticks(delta: int) -> None:
    """Posune simulovaný čas o delta milisekund."""
    global _fake_ticks
    _fake_ticks = (_fake_ticks + int(delta)) % _TICKS_PERIOD
