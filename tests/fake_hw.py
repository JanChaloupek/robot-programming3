class FakeI2C:
    def __init__(self):
        self.locked = False
        self.writes = []
        self.reads = []
    def try_lock(self):
        if not self.locked:
            self.locked = True
            return True
        return False
    def unlock(self):
        self.locked = False
    def scan(self):
        return [0x38, 0x62]
    def readfrom_into(self, addr, buf, start=0, end=None):
        data = self.reads.pop(0) if self.reads else [0]
        for i in range(len(buf)):
            buf[i] = data[i] if i < len(data) else 0
    def writeto(self, addr, buf):
        self.writes.append((addr, list(buf)))
    def writeto_then_readfrom(self, addr, wbuf, rbuf):
        self.writes.append((addr, list(wbuf)))
        self.readfrom_into(addr, rbuf)

def ticks_ms():
    return 1000

def ticks_diff(a, b):
    return a - b

class FakeDisplay:
    def pixel(self, *args):
        pass

class FakeLED:
    def toggle(self):
        pass
    def off(self):
        pass

class FakeButton:
    def is_pressed(self):
        return False
