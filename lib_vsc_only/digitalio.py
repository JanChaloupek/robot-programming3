"""
digitalio.py – společný stub pro VS Code a fake hardware pro testy.

Tento modul napodobuje CircuitPython modul `digitalio`, který poskytuje
práci s digitálními piny (GPIO) – vstupy, výstupy, pull-up/pull-down
rezistory a čtení/zápis logických hodnot.

V této verzi:
- modul je určený pro vývoj na PC (VS Code / Pylance)
- funguje jako fake hardware pro unit testy
- nevyžaduje žádný skutečný mikrořadič ani GPIO
- chová se deterministicky a ukládá historii změn

Reálný modul `digitalio` je součástí CircuitPythonu a není dostupný na PC.
Tento soubor slouží pouze pro výuku, vývoj a testování.
"""


class Direction:
    """
    Enum-like třída reprezentující směr digitálního pinu.

    V reálném CircuitPythonu:
        - Direction.INPUT  – pin je vstup
        - Direction.OUTPUT – pin je výstup

    V této fake verzi:
        - hodnoty jsou pouze symbolické (0/1)
        - používají se pro testování a VS Code autocomplete
    """
    INPUT = 0
    OUTPUT = 1


class Pull:
    """
    Enum-like třída reprezentující pull-up/pull-down rezistory.

    V reálném CircuitPythonu:
        - Pull.UP   – aktivuje interní pull-up rezistor
        - Pull.DOWN – aktivuje interní pull-down rezistor

    V této fake verzi:
        - hodnoty jsou pouze symbolické (0/1)
        - používají se pro testování a VS Code autocomplete
    """
    UP = 0
    DOWN = 1


class DigitalInOut:
    """
    Fake verze třídy DigitalInOut z CircuitPythonu.

    V reálném zařízení:
        - DigitalInOut umožňuje číst a zapisovat digitální hodnoty
        - pin může být INPUT nebo OUTPUT
        - INPUT může mít pull-up nebo pull-down
        - OUTPUT může zapisovat True/False (HIGH/LOW)

    V této fake verzi:
        - směr pinu se ukládá do self.direction
        - pull-up/pull-down se ukládá do self.pull
        - hodnota pinu je v self.value (True/False)
        - všechny zápisy se ukládají do write_history
        - chování je deterministické a vhodné pro testy

    Atributy:
        pin           – symbolický pin (např. board.P0)
        direction     – Direction.INPUT nebo Direction.OUTPUT
        pull          – Pull.UP, Pull.DOWN nebo None
        value         – logická hodnota pinu (True/False)
        write_history – seznam všech změn hodnoty (pro testy)
    """

    def __init__(self, pin):
        """
        Inicializuje fake digitální pin.

        Parametry:
            pin – libovolný objekt reprezentující pin (např. board.P0)
        """
        self.pin = pin
        self.direction = None
        self.pull = None
        self.value = False
        self.write_history = []

    def switch_to_output(self, value=False):
        """
        Přepne pin do režimu OUTPUT a nastaví počáteční hodnotu.

        Parametry:
            value – počáteční logická hodnota (True/False)

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
        Zde nedělá nic.
        """
        pass
