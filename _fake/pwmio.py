"""
Fake implementace CircuitPython modulu `pwmio`.

Tento modul simuluje PWM výstupy (Pulse Width Modulation) pro vývoj na PC.
Je určený pro výuku a unit testy, kde není dostupný skutečný hardware.

Vlastnosti fake verze:
- podporuje přímé přiřazení duty_cycle a frequency (stejně jako CircuitPython)
- ukládá všechny změny do history pro snadné testování
- negeneruje žádný skutečný signál
- chová se deterministicky
"""

class PWMOut:
    """
    Fake verze třídy PWMOut z CircuitPythonu.

    V reálném zařízení:
        - PWMOut generuje PWM signál na daném pinu
        - duty_cycle je 16bitová hodnota (0–65535)
        - frequency určuje frekvenci PWM signálu
        - změny se provádějí přímým přiřazením atributů

    Ve fake verzi:
        - duty_cycle a frequency se ukládají do interních atributů
        - každá změna se zapisuje do history
        - žádný skutečný signál se negeneruje

    Atributy:
        pin         – symbolický pin (např. board.P0)
        frequency   – aktuální frekvence PWM (Hz)
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

        Počáteční stav se uloží do history.
        """
        self.pin = pin
        self._frequency = frequency
        self._duty_cycle = duty_cycle

        # historie změn (frequency, duty_cycle)
        self.history = [(frequency, duty_cycle)]

    def deinit(self):
        """
        Fake uvolnění PWM kanálu.

        V reálném zařízení by uvolnilo hardware.
        Zde nedělá nic.
        """
        pass

    @property
    def duty_cycle(self):
        """Aktuální šířka pulzu (0–65535)."""
        return self._duty_cycle

    @duty_cycle.setter
    def duty_cycle(self, value):
        """Nastaví novou šířku pulzu a uloží změnu do history."""
        self._duty_cycle = value
        self.history.append((self._frequency, value))

    @property
    def frequency(self):
        """Aktuální frekvence PWM v Hz."""
        return self._frequency

    @frequency.setter
    def frequency(self, value):
        """Nastaví novou frekvenci a uloží změnu do history."""
        self._frequency = value
        self.history.append((value, self._duty_cycle))
