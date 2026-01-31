# ================================
# _fake/digitalio.py
# ================================

"""
Fake implementace CircuitPython modulu `digitalio`.

Simuluje digitální piny (GPIO) pro vývoj a testování na PC.
Chování je deterministické a ukládá historii změn, aby bylo možné
psát přesné unit testy bez skutečného hardware.
"""

class Direction:
    """
    Enum-like třída reprezentující směr digitálního pinu.

    - Direction.INPUT  – pin je vstup
    - Direction.OUTPUT – pin je výstup
    """
    INPUT = 0
    OUTPUT = 1


class Pull:
    """
    Enum-like třída reprezentující pull-up/pull-down rezistory.

    - Pull.UP   – aktivuje interní pull-up rezistor
    - Pull.DOWN – aktivuje interní pull-down rezistor
    """
    UP = 0
    DOWN = 1


class DigitalInOut:
    """
    Fake verze třídy DigitalInOut z CircuitPythonu.

    Vlastnosti:
        pin           – symbolický pin (např. board.P0)
        direction     – Direction.INPUT nebo Direction.OUTPUT
        pull          – Pull.UP, Pull.DOWN nebo None
        value         – logická hodnota pinu (True/False)
        write_history – seznam všech změn hodnoty (pro testy)

    Chování:
        - switch_to_output() nastaví směr a hodnotu
        - switch_to_input() nastaví směr a pull rezistor
        - write_history ukládá všechny změny výstupní hodnoty
    """

    def __init__(self, pin):
        self.pin = pin
        self.direction = None
        self.pull = None
        self.value = False
        self.write_history = []

    def switch_to_output(self, value=False):
        """
        Přepne pin do režimu OUTPUT a nastaví počáteční hodnotu.

        Uloží záznam do write_history:
            ("set", value)
        """
        self.direction = Direction.OUTPUT
        self.value = value
        self.write_history.append(("set", value))

    def switch_to_input(self, pull=None):
        """
        Přepne pin do režimu INPUT.

        Parametry:
            pull – Pull.UP, Pull.DOWN nebo None
        """
        self.direction = Direction.INPUT
        self.pull = pull

    def deinit(self):
        """
        Dummy metoda pro kompatibilitu s CircuitPythonem.
        V reálném zařízení uvolňuje pin.
        """
        pass
