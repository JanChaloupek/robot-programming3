"""
battery – měření napětí baterie robota JoyCar.

Studentům:
- JoyCar má na PIN2 odporový dělič → lze měřit napětí baterie.
- Samotný pico:ed to neumí → pokud JoyCar není připojen, funkce vrací None.
"""

from analogio import AnalogIn
from board import P2

_MAGIC = 0.000147


def battery_voltage():
    """
    Vrací napětí baterie JoyCaru v Voltech.
    Pokud JoyCar není připojen, vrací None.
    """
    pin = AnalogIn(P2)
    raw = pin.value

    # pico:ed samotný vrací velmi nízké hodnoty
    if raw < 500:
        return None

    return raw * _MAGIC
