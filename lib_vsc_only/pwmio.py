"""
pwmio.py – společný stub pro VS Code a fake hardware pro testy.

Tento modul napodobuje CircuitPython modul `pwmio`, který poskytuje
PWM výstupy (Pulse Width Modulation) pro řízení motorů, LED, serv a dalších
zařízení.

V této verzi:
- modul je určený pro vývoj na PC (VS Code / Pylance)
- funguje jako fake hardware pro unit testy
- nevyžaduje žádný skutečný mikrořadič ani PWM periférii
- chová se deterministicky a ukládá historii změn

Reálný modul `pwmio` je součástí CircuitPythonu a není dostupný na PC.
Tento soubor slouží pouze pro výuku, vývoj a testování.
"""


class PWMOut:
    """
    Fake verze třídy PWMOut z CircuitPythonu.

    V reálném zařízení:
        - PWMOut generuje PWM signál na daném pinu
        - duty_cycle je 16bitová hodnota (0–65535)
        - frequency určuje frekvenci PWM signálu

    V této fake verzi:
        - duty_cycle a frequency se pouze ukládají do atributů
        - žádný skutečný signál se negeneruje
        - všechny změny se ukládají do history (užitečné pro testy)

    Atributy:
        pin         – symbolický pin (např. board.P0)
        frequency   – aktuální frekvence PWM
        duty_cycle  – aktuální šířka pulzu (0–65535)
        history     – seznam všech změn (frequency, duty_cycle)
    """

    def __init__(self, pin, *, frequency=5000, duty_cycle=0):
        """
        Inicializuje fake PWM výstup.

        Parametry:
            pin         – libovolný objekt reprezentující pin
            frequency   – počáteční frekvence PWM
            duty_cycle  – počáteční šířka pulzu

        Uloží počáteční stav do history.
        """
        self.pin = pin
        self.frequency = frequency
        self.duty_cycle = duty_cycle

        # Pro testy: historie všech změn
        self.history = [(frequency, duty_cycle)]

    def deinit(self):
        """
        Dummy metoda pro kompatibilitu s CircuitPythonem.

        V reálném zařízení uvolňuje PWM kanál.
        Zde nedělá nic.
        """
        pass

    def set_duty_cycle(self, value):
        """
        Nastaví novou hodnotu duty_cycle.

        Parametry:
            value – nová šířka pulzu (0–65535)

        Uloží změnu do history.
        """
        self.duty_cycle = value
        self.history.append((self.frequency, value))

    def set_frequency(self, value):
        """
        Nastaví novou frekvenci PWM.

        Parametry:
            value – nová frekvence v Hz

        Uloží změnu do history.
        """
        self.frequency = value
        self.history.append((value, self.duty_cycle))
