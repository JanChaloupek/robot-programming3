# _stubs/board.pyi

"""
Stub rozhraní pro modul `board` z CircuitPythonu.

Poskytuje symbolické názvy pinů (např. board.P0, board.SCL).
"""

class _Pin:
    """
    Reprezentace pinu v CircuitPythonu.

    Atributy:
        name: str – název pinu (např. "P0", "SCL")
    """
    name: str
    def __init__(self, name: str): ...
    def __repr__(self) -> str: ...

# Digitální piny
P0: _Pin
P1: _Pin
P2: _Pin
P3: _Pin
P4: _Pin
P5: _Pin
P6: _Pin
P7: _Pin
P8: _Pin
P9: _Pin
P10: _Pin
P11: _Pin
P12: _Pin
P13: _Pin
P14: _Pin
P15: _Pin
P16: _Pin
P17: _Pin
P18: _Pin
P19: _Pin
P20: _Pin

# Speciální piny
BUZZER: _Pin
BUTTON_A: _Pin
BUTTON_B: _Pin
LED: _Pin

BUZZER_GP0: _Pin
I2C0_SCL: _Pin
I2C0_SDA: _Pin

# Alias
SCL: _Pin
SDA: _Pin
