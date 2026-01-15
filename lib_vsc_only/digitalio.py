# digitalio.py – stub for CircuitPython digitalio module

class Direction:
    INPUT = 0
    OUTPUT = 1

class Pull:
    UP = 0
    DOWN = 1

class DigitalInOut:
    def __init__(self, pin):
        self.direction = None
        self.pull = None
        self.value = False
