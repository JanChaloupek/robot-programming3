# busio.py – minimal stub for CircuitPython busio
# Allows VS Code / Pylance to resolve symbols without hardware.

class I2C:
    def __init__(self, scl=None, sda=None, frequency=400000):
        pass

    def try_lock(self):
        return True

    def unlock(self):
        pass

    def scan(self):
        return []

    def readfrom_into(self, address, buffer, *, start=0, end=None):
        pass

    def writeto(self, address, buffer, *, start=0, end=None, stop=True):
        pass

    def writeto_then_readfrom(self, address, out_buffer, in_buffer, *,
                            out_start=0, out_end=None,
                            in_start=0, in_end=None):
        pass

class SPI:
    def __init__(self, clock=None, MOSI=None, MISO=None):
        pass

    def try_lock(self):
        return True

    def unlock(self):
        pass

    def configure(self, *, baudrate=1000000, polarity=0, phase=0, bits=8):
        pass

    def write(self, data):
        pass

    def readinto(self, buffer):
        pass

    def write_readinto(self, out_buffer, in_buffer):
        pass


class UART:
    def __init__(self, tx=None, rx=None, baudrate=9600, bits=8, parity=None, stop=1):
        pass

    def read(self, nbytes=None):
        return None

    def readinto(self, buffer):
        return None

    def write(self, data):
        return len(data) if data else 0

    def any(self):
        return 0
