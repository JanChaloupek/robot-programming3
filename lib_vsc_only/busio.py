"""
busio.py – společný stub pro VS Code a fake hardware pro testy.

Tento modul napodobuje CircuitPython modul `busio`, který poskytuje
rozhraní pro I2C, SPI a UART komunikaci.

V této verzi:
- modul je určený pro vývoj na PC (VS Code / Pylance)
- funguje jako fake hardware pro unit testy
- nevyžaduje žádný skutečný mikrořadič ani sběrnici
- chová se deterministicky a umožňuje testům kontrolovat komunikaci

Reálný modul `busio` je součástí CircuitPythonu a není dostupný na PC.
Tento soubor slouží pouze pro výuku, vývoj a testování.
"""


# ---------------------------------------------------------
# Fake I2C
# ---------------------------------------------------------

class I2C:
    """
    Fake verze třídy I2C z CircuitPythonu.

    V reálném zařízení:
        - I2C komunikuje s periferiemi (senzory, expandéry, LED drivery)
        - používá fyzické piny SCL a SDA
        - podporuje čtení, zápis a kombinované operace

    V této fake verzi:
        - všechny operace jsou simulované
        - testy mohou vkládat data pro čtení pomocí queue_read()
        - všechny zápisy se ukládají do write_history
        - všechny čtecí operace se ukládají do read_history
        - scan() vrací deterministické adresy (0x38, 0x62)

    Atributy:
        scl, sda        – symbolické piny
        frequency       – I2C frekvence (ignorováno)
        write_history   – seznam všech zápisů (adresa, data)
        read_history    – seznam adres, ze kterých se četlo
        _fake_reads     – fronta dat, která se vrátí při čtení
    """

    def __init__(self, scl=None, sda=None, frequency=400000):
        self.scl = scl
        self.sda = sda
        self.frequency = frequency

        self.write_history = []
        self.read_history = []
        self._fake_reads = []

    def try_lock(self):
        """Fake: vždy úspěšné uzamčení sběrnice."""
        return True

    def unlock(self):
        """Fake: nic nedělá."""
        pass

    def scan(self):
        """
        Fake implementace I2C scan.

        Vrací deterministické adresy používané v testech:
            - 0x38 (PCF8574)
            - 0x62 (PCA9633)
        """
        return [0x38, 0x62]

    def queue_read(self, data: bytes):
        """
        Test helper: vloží data, která se vrátí při příštím čtení.

        Příklad:
            i2c.queue_read(b"\x12\x34")
        """
        self._fake_reads.append(bytes(data))
        # print("queue_read ", data, self._fake_reads)

    def readfrom_into(self, address, buffer, *, start=0, end=None):
        """
        Fake čtení z I2C.

        - uloží adresu do read_history
        - pokud jsou ve frontě data, použije je
        - jinak vrátí nuly
        """
        # print("readfrom_into", hex(address), buffer, start, end)
        self.read_history.append(address)

        if not self._fake_reads:
            data = bytes([0] * len(buffer))
            # print("readfrom_into data1", data)
        else:
            data = self._fake_reads.pop(0)
            # print("readfrom_into data2", data)

        if end is None:
            end = len(buffer)
        # print("readfrom_into end", end)

        for i in range(start, end):
            # print(i, start, end, data)
            buffer[i] = data[i - start]

    def writeto(self, address, buffer, *, start=0, end=None, stop=True):
        """
        Fake zápis na I2C.

        Uloží do write_history dvojici:
            (adresa, data)
        """
        if end is None:
            end = len(buffer)
        data = bytes(buffer[start:end])
        self.write_history.append((address, data))

    def writeto_then_readfrom(self, address, out_buffer, in_buffer, *,
                              out_start=0, out_end=None,
                              in_start=0, in_end=None):
        """
        Fake kombinovaná operace:
            1) zápis
            2) čtení
        """
        self.writeto(address, out_buffer, start=out_start, end=out_end)
        self.readfrom_into(address, in_buffer, start=in_start, end=in_end)


# ---------------------------------------------------------
# Fake SPI
# ---------------------------------------------------------

class SPI:
    """
    Fake verze SPI sběrnice.

    V reálném zařízení:
        - SPI slouží pro rychlou komunikaci s displeji, pamětmi atd.

    V této fake verzi:
        - write() ukládá data do write_history
        - readinto() plní buffer nulami
        - write_readinto() kombinuje obojí
    """

    def __init__(self, clock=None, MOSI=None, MISO=None):
        self.clock = clock
        self.MOSI = MOSI
        self.MISO = MISO

        self.write_history = []
        self.read_history = []

    def try_lock(self):
        return True

    def unlock(self):
        pass

    def configure(self, *, baudrate=1000000, polarity=0, phase=0, bits=8):
        """Fake konfigurace SPI – uloží parametry do self.config."""
        self.config = (baudrate, polarity, phase, bits)

    def write(self, data):
        """Uloží data do write_history."""
        self.write_history.append(bytes(data))

    def readinto(self, buffer):
        """Naplní buffer nulami a uloží délku do read_history."""
        for i in range(len(buffer)):
            buffer[i] = 0
        self.read_history.append(len(buffer))

    def write_readinto(self, out_buffer, in_buffer):
        """Kombinace write() a readinto()."""
        self.write(out_buffer)
        self.readinto(in_buffer)


# ---------------------------------------------------------
# Fake UART
# ---------------------------------------------------------

class UART:
    """
    Fake verze UART rozhraní.

    V reálném zařízení:
        - UART slouží pro sériovou komunikaci (GPS, modemy, debug)

    V této fake verzi:
        - write() ukládá data do write_history
        - read() vrací data z fronty read_queue
        - readinto() zapisuje data do bufferu
        - any() vrací počet dostupných bajtů
    """

    def __init__(self, tx=None, rx=None, baudrate=9600, bits=8, parity=None, stop=1):
        self.tx = tx
        self.rx = rx
        self.baudrate = baudrate

        self.write_history = []
        self.read_queue = []

    def queue_read(self, data: bytes):
        """
        Test helper: vloží data, která se vrátí při příštím read().

        Příklad:
            uart.queue_read(b"OK")
        """
        self.read_queue.append(bytes(data))

    def read(self, nbytes=None):
        """Vrátí další položku z read_queue nebo None."""
        if not self.read_queue:
            return None
        return self.read_queue.pop(0)

    def readinto(self, buffer):
        """Zapíše data z read() do bufferu."""
        data = self.read(nbytes=len(buffer))
        if data is None:
            return None
        for i in range(len(buffer)):
            buffer[i] = data[i]
        return len(buffer)

    def write(self, data):
        """Uloží data do write_history a vrátí počet zapsaných bajtů."""
        if data:
            self.write_history.append(bytes(data))
            return len(data)
        return 0

    def any(self):
        """Vrací počet dostupných bajtů v read_queue."""
        return len(self.read_queue)
