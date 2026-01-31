"""
Fake busio modul pro testy JoyCar.

Plně kompatibilní s testy:
- write_history
- read_history
- queue_read()
- scan()
- deinit()
- writeto()
- readfrom_into()
"""

class I2C:
    def __init__(self, scl=None, sda=None, frequency=400000):
        self.scl = scl
        self.sda = sda
        self.frequency = frequency

        # Testy očekávají tyto struktury:
        self.write_history = []   # seznam: (addr, bytes)
        self.read_history = []    # seznam: (addr, length)
        self._read_queue = []     # fronta hodnot pro readfrom_into()

        # Testy očekávají, že scan() vrátí zařízení,
        # která byla použita ve write_history nebo queue_read.
        self._known_devices = {0x38, 0x62}

    # ---------------------------------------------------------
    # Kompatibilita s CircuitPythonem
    # ---------------------------------------------------------
    def deinit(self):
        pass

    def try_lock(self):
        return True

    def unlock(self):
        pass

    # ---------------------------------------------------------
    # Testovací API
    # ---------------------------------------------------------
    def queue_read(self, data):
        """
        Přidá hodnoty do fronty pro readfrom_into().
        data může být list nebo bytes.
        """
        if isinstance(data, int):
            self._read_queue.append(bytes([data]))
        else:
            self._read_queue.append(bytes(data))

    # ---------------------------------------------------------
    # I2C API
    # ---------------------------------------------------------
    def scan(self):
        """Vrací seznam známých zařízení."""
        return sorted(self._known_devices)

    def writeto(self, addr, data, *, stop=True):
        """Uloží zápis do write_history."""
        b = bytes(data)
        self.write_history.append((addr, b))
        self._known_devices.add(addr)

    def readfrom_into(self, addr, buf, *, stop=True):
        """Naplní buffer hodnotami z queue_read."""
        self.read_history.append((addr, len(buf)))
        self._known_devices.add(addr)

        if not self._read_queue:
            # Pokud není nic ve frontě, vrací nuly
            for i in range(len(buf)):
                buf[i] = 0
            return

        data = self._read_queue.pop(0)
        for i in range(len(buf)):
            buf[i] = data[i] if i < len(data) else 0
