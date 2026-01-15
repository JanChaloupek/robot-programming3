# pwmio.py – stub for CircuitPython pwmio module

class PWMOut:
    def __init__(self, pin, *, frequency=5000, duty_cycle=0):
        self.frequency = frequency
        self.duty_cycle = duty_cycle

    def deinit(self):
        pass
