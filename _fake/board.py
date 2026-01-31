# _fake/board.py

"""
Fake implementace CircuitPython modulu `board`.

Poskytuje symbolické názvy pinů (P0–P20, SCL, SDA, BUTTON_A, …)
pro vývoj a testování na PC.
"""

class _Pin:
    """
    Jednoduchá reprezentace pinu.

    - pin je pouze pojmenovaný objekt
    - slouží jako identifikátor pro testy a VS Code
    - __repr__ zobrazuje název pinu
    """

    def __init__(self, name: str):
        self.name = name

    def __repr__(self):
        return f"<Pin {self.name}>"

# Digitální piny P0–P20
P0 = _Pin("P0")
P1 = _Pin("P1")
P2 = _Pin("P2")
P3 = _Pin("P3")
P4 = _Pin("P4")
P5 = _Pin("P5")
P6 = _Pin("P6")
P7 = _Pin("P7")
P8 = _Pin("P8")
P9 = _Pin("P9")
P10 = _Pin("P10")
P11 = _Pin("P11")
P12 = _Pin("P12")
P13 = _Pin("P13")
P14 = _Pin("P14")
P15 = _Pin("P15")
P16 = _Pin("P16")
P17 = _Pin("P17")
P18 = _Pin("P18")
P19 = _Pin("P19")
P20 = _Pin("P20")

# Speciální piny
BUZZER = _Pin("BUZZER")
BUTTON_A = _Pin("BUTTON_A")
BUTTON_B = _Pin("BUTTON_B")
LED = _Pin("LED")

BUZZER_GP0 = _Pin("BUZZER_GP0")
I2C0_SCL = _Pin("I2C0_SCL")
I2C0_SDA = _Pin("I2C0_SDA")

# Alias pro I2C piny
SCL = P19
SDA = P20
