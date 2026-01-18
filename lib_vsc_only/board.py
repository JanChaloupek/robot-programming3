"""
board.py – společný stub pro VS Code a fake hardware pro testy.

Tento modul napodobuje CircuitPython modul `board`, který na reálném
mikrořadiči poskytuje symbolické názvy pinů (např. board.P0, board.SCL).

V této verzi:
- modul je určený pro vývoj na PC (VS Code / Pylance)
- funguje jako fake hardware pro unit testy
- poskytuje pojmenované objekty reprezentující jednotlivé piny
- neobsahuje žádné skutečné GPIO operace
- je plně kompatibilní s importy typu `import board`

Reálný modul `board` je součástí CircuitPythonu a není dostupný na PC.
Tento soubor slouží pouze pro výuku, vývoj a testování.
"""


class _Pin:
    """
    Jednoduchá reprezentace pinu.

    V reálném CircuitPythonu:
        - objekty pinů obsahují metadata a jsou napojeny na hardware

    V této fake verzi:
        - pin je pouze pojmenovaný objekt
        - slouží jako identifikátor pro testy a VS Code
        - jeho jméno se zobrazuje v __repr__ pro snadné ladění

    Atributy:
        name – textový název pinu (např. "P0", "SCL", "BUTTON_A")
    """

    def __init__(self, name):
        self.name = name

    def __repr__(self):
        return f"<Pin {self.name}>"


# ---------------------------------------------------------
# Digitální piny P0–P20 (odpovídají pico:ed / micro:bit stylu)
# ---------------------------------------------------------

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


# ---------------------------------------------------------
# Symbolické názvy speciálních pinů (kompatibilní s pico:ed API)
# ---------------------------------------------------------

BUZZER = _Pin("BUZZER")
BUTTON_A = _Pin("BUTTON_A")
BUTTON_B = _Pin("BUTTON_B")
LED = _Pin("LED")

BUZZER_GP0 = _Pin("BUZZER_GP0")
I2C0_SCL = _Pin("I2C0_SCL")
I2C0_SDA = _Pin("I2C0_SDA")


# ---------------------------------------------------------
# Alias pro I2C piny (odpovídá CircuitPythonu)
# ---------------------------------------------------------

SCL = P19
SDA = P20
