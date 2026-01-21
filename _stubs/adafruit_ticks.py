"""
adafruit_ticks.py – společný stub pro VS Code a fake hardware pro testy.

Tento modul napodobuje chování CircuitPython knihovny `adafruit_ticks`,
která poskytuje monotónní časovač založený na milisekundách.

V reálném CircuitPythonu:
- `ticks_ms()` vrací stále rostoucí čas v ms (s přetečením po ~6 dnech)
- `ticks_add()` a `ticks_diff()` řeší přetečení bezpečným způsobem
- používá se pro časování, periodické úlohy, debounce tlačítek atd.

V této verzi:
- modul je deterministický (ticks_ms vrací hodnotu řízenou testy)
- je vhodný pro VS Code / Pylance (autocomplete, typy)
- je vhodný pro unit testy (žádný skutečný čas, žádné čekání)
- studenti mohou modul používat stejně jako na reálném zařízení

Reálný modul `adafruit_ticks` je součástí CircuitPythonu a není dostupný na PC.
Tento soubor slouží pro výuku, vývoj a testování.
"""

# ---------------------------------------------------------
# Konstanty (stejné jako v MicroPythonu, ale dummy hodnoty)
# ---------------------------------------------------------

_TICKS_PERIOD = 1 << 29
_TICKS_MAX = _TICKS_PERIOD - 1
_TICKS_HALFPERIOD = _TICKS_PERIOD // 2

# Interní simulovaný čas (v milisekundách)
# Testy mohou měnit tuto hodnotu pomocí set_ticks_ms()
_fake_ticks = 0


# ---------------------------------------------------------
# Veřejné API – stejné jako v MicroPythonu
# ---------------------------------------------------------

def ticks_ms() -> int:
    """
    Vrátí aktuální simulovaný čas v milisekundách.

    Na reálném zařízení:
        - vrací monotónní čas od startu programu
        - hodnota přeteče po ~6 dnech

    V této fake verzi:
        - čas se NEZVYŠUJE automaticky
        - testy nebo kód mohou čas posouvat pomocí set_ticks_ms() nebo advance_ticks()

    Příklad:
        >>> import adafruit_ticks as ticks
        >>> ticks.set_ticks_ms(100)
        >>> ticks.ticks_ms()
        100
    """
    return _fake_ticks


def ticks_add(ticks: int, delta: int) -> int:
    """
    Vrátí ticks + delta s bezpečným přetečením.

    Používá se pro výpočet budoucích časů:
        next_time = ticks_add(ticks_ms(), 200)

    Chová se stejně jako MicroPython implementace.
    """
    return (ticks + delta) % _TICKS_PERIOD


def ticks_diff(ticks1: int, ticks2: int) -> int:
    """
    Vrátí rozdíl dvou tick hodnot.

    Výsledek je v rozsahu:
        -_TICKS_HALFPERIOD .. +_TICKS_HALFPERIOD

    To umožňuje bezpečné porovnávání i při přetečení.

    Příklad:
        >>> ticks_diff(10, 5)
        5
        >>> ticks_diff(5, 10)
        -5
    """
    diff = (ticks1 - ticks2) & _TICKS_MAX
    diff = ((diff + _TICKS_HALFPERIOD) & _TICKS_MAX) - _TICKS_HALFPERIOD
    return diff


def ticks_less(ticks1: int, ticks2: int) -> bool:
    """
    Vrátí True, pokud ticks1 je "dříve" než ticks2.

    Používá se pro porovnávání časů:
        if ticks_less(now, deadline):
            ...

    Příklad:
        >>> ticks_less(5, 10)
        True
        >>> ticks_less(10, 5)
        False
    """
    return ticks_diff(ticks1, ticks2) < 0


# ---------------------------------------------------------
# FakeHW rozšíření – užitečné pro testy
# ---------------------------------------------------------

def set_ticks_ms(value: int) -> None:
    """
    Nastaví simulovaný čas v milisekundách.

    Testy mohou ručně řídit čas:
        >>> ticks.set_ticks_ms(500)
        >>> ticks.ticks_ms()
        500
    """
    global _fake_ticks
    _fake_ticks = int(value)


def advance_ticks(delta: int) -> None:
    """
    Posune simulovaný čas o delta milisekund.

    Užitečné pro testování časovačů, Period, Timer atd.

    Příklad:
        >>> ticks.set_ticks_ms(0)
        >>> ticks.advance_ticks(50)
        >>> ticks.ticks_ms()
        50
    """
    global _fake_ticks
    _fake_ticks = (_fake_ticks + int(delta)) % _TICKS_PERIOD
