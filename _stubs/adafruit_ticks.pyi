# _stubs/adafruit_ticks.pyi

"""
Stub rozhraní pro modul adafruit_ticks z CircuitPythonu.

Poskytuje monotónní časovač založený na milisekundách.
"""

def ticks_ms() -> int:
    """
    Vrací monotónní čas v milisekundách.
    Hodnota přeteče po několika dnech.
    """
    ...

def ticks_add(ticks: int, delta: int) -> int:
    """
    Vrací ticks + delta s bezpečným přetečením.
    """
    ...

def ticks_diff(ticks1: int, ticks2: int) -> int:
    """
    Vrací rozdíl dvou tick hodnot v rozsahu
    -HALFPERIOD .. +HALFPERIOD.
    """
    ...

def ticks_less(ticks1: int, ticks2: int) -> bool:
    """
    Vrací True, pokud ticks1 je dříve než ticks2.
    """
    ...
