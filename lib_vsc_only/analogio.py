"""
analogio.py – společný stub pro VS Code a fake hardware pro testy.

Tento modul napodobuje část API CircuitPython knihovny `analogio`,
která poskytuje přístup k analogovým vstupům (ADC).

V této verzi:
- modul je určený pro vývoj na PC (VS Code / Pylance)
- funguje jako fake hardware pro unit testy
- nevyžaduje žádný skutečný mikrořadič ani ADC
- chová se deterministicky (hodnoty se nastavují ručně)

Reálný modul `analogio` je součástí CircuitPythonu a není dostupný na PC.
Tento soubor slouží pouze pro výuku, vývoj a testování.
"""


class AnalogIn:
    """
    Fake verze třídy AnalogIn z CircuitPythonu.

    V reálném zařízení:
        - AnalogIn čte hodnotu z ADC (0–65535)
        - hodnota se mění podle napětí na pinu

    V této fake verzi:
        - hodnota je uložena v atributu `value`
        - testy ji mohou libovolně nastavovat
        - metoda read() pouze vrací tuto hodnotu
        - čtení je deterministické a bez šumu

    Atributy:
        pin         – identifikátor pinu (libovolný objekt)
        value       – aktuální simulovaná ADC hodnota (0–65535)
        read_count  – počet volání read(), užitečné pro testy
    """

    def __init__(self, pin):
        """
        Inicializuje fake ADC vstup.

        Parametry:
            pin – libovolný objekt reprezentující pin (např. board.P0)
        """
        self.pin = pin
        self.value = 0          # simulovaná ADC hodnota
        self.read_count = 0     # počet čtení (pro testy)

    def deinit(self):
        """
        Dummy metoda pro kompatibilitu s CircuitPythonem.

        V reálném zařízení uvolňuje ADC kanál.
        Zde nedělá nic.
        """
        pass

    def read(self):
        """
        Vrátí aktuální simulovanou hodnotu ADC.

        V reálném CircuitPythonu:
            - read() vrací hodnotu 0–65535
            - může obsahovat šum nebo být filtrována

        V této fake verzi:
            - vrací přesně hodnotu uloženou v self.value
            - inkrementuje read_count (užitečné pro testy)
        """
        self.read_count += 1
        return self.value
