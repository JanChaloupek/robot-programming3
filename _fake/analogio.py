# _fake/analogio.py

class AnalogIn:
    """
    Fake verze třídy AnalogIn z CircuitPythonu.

    - hodnota ADC je uložena v `value`
    - testy ji mohou libovolně nastavovat
    - read() vrací přesně tuto hodnotu
    - read_count sleduje počet čtení
    """
    default_value = 0

    def __init__(self, pin):
        self.pin = pin
        self.value = AnalogIn.default_value
        self.read_count = 0

    def deinit(self):
        pass

    def read(self):
        self.read_count += 1
        return self.value
