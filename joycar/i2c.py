"""
i2c.py – bezpečný wrapper pro I2C komunikaci JoyCar robota.

Tento modul poskytuje třídu I2C, která obaluje hardwarový i2c a zajišťuje:
- bezpečné zamykání sběrnice pomocí context manageru,
- jednotné API pro všechny I2C periferie robota,
- kompatibilitu s fake hardwarem v lib_vsc_only.

Použití:
    from joycar.i2c import I2C
    from picoed import i2c as pico_i2c

    i2c = I2C(pico_i2c)
"""

from adafruit_ticks import ticks_ms, ticks_diff
from busio import I2C as BusIO_I2C
from utils.log import log


class I2C:
    """
    Bezpečný wrapper pro I2C komunikaci.

    Používá se výhradně přes `with i2c:` aby bylo zajištěno:
    - automatické zamknutí sběrnice,
    - automatické odemknutí sběrnice,
    - jednotné chování na reálném i fake hardware.

    Atributy:
        i2c (BusIO_I2C): Podkladový I2C objekt.
    """

    def __init__(self, i2c: BusIO_I2C) -> None:
        self._hw_i2c = i2c

    # ---------------------------------------------------------
    # Context manager
    # ---------------------------------------------------------
    def __enter__(self) -> "I2C":
        self._lock()
        return self

    def __exit__(self, exc_type, exc_value, traceback) -> bool:
        self._unlock()
        return False

    # ---------------------------------------------------------
    # Lock / unlock
    # ---------------------------------------------------------
    def _lock(self) -> None:
        """Zajistí I2C lock (čeká, dokud není dostupný)."""
        if self._hw_i2c.try_lock():
            return

        start = ticks_ms()
        while not self._hw_i2c.try_lock():
            if ticks_diff(ticks_ms(), start) > 5:
                e = TimeoutError("I2C lock timeout")
                log.exception(e)
                raise e

    def _unlock(self) -> None:
        """Uvolní I2C lock."""
        self._hw_i2c.unlock()

    # ---------------------------------------------------------
    # Veřejné metody — bez locku
    # ---------------------------------------------------------
    def scan(self) -> list[int]:
        """Vrátí seznam dostupných I2C adres."""
        return self._hw_i2c.scan()

    def read(self, addr: int, n: int) -> bytearray:
        """Přečte n bajtů z adresy."""
        buffer = bytearray(n)
        self._hw_i2c.readfrom_into(addr, buffer)
        return buffer

    def write(self, addr: int, buf: bytearray) -> None:
        """Zapíše buffer na adresu."""
        self._hw_i2c.writeto(addr, buf)

    def write_readinto(self, addr: int, write_buf: bytearray, read_buf: bytearray) -> None:
        """Zapíše a následně přečte data z adresy."""
        self._hw_i2c.writeto_then_readfrom(addr, write_buf, read_buf)