"""
pca9685.py – Ovladač 16kanálového 12bitového PWM generátoru PCA9685.

Tento modul slouží jako náhrada původního čipu PCA9633 při spálení H-můstku
nebo při přechodu na výkonnější řízení motorů (např. přes modul L298N):
- Rozlišení: 12 bitů (hodnoty PWM 0–4095).
- Řízení směru: Každý motor používá dva PWM kanály (channel a channel+1):
    - Kanál 0 a 1: Pravý motor
    - Kanál 2 a 3: Levý motor
"""

from typing import Any


class PCA9685:
    """Ovladač I2C PWM generátoru PCA9685 pro řízení motorů JoyCaru."""

    MAX_PWM = 4095

    # Významné registry čipu PCA9685:
    RegMODE1 = 0x00         # Řídicí registr režimu 1 (řízení spánku a auto-incrementu)
    RegMODE1_VALUE = 0x20   # Běžný provoz s povoleným auto-incrementem adres registrů
    RegMODE2 = 0x01         # Řídicí registr režimu 2
    RegPwm00 = 0x06         # Začátek registrů kanálu 0 (ON_L, ON_H, OFF_L, OFF_H)

    def __init__(self, i2c: Any, address: int = 0x61) -> None:
        """
        Inicializace PCA9685.

        Args:
            i2c (Any): I2C sběrnice (joycar.i2c.I2C nebo busio.I2C).
            address (int): I2C adresa modulu (výchozí 0x61, případně 0x40).
        """
        self._i2c = i2c
        self._address = address

    def _writeBytes(self, data: bytes) -> None:
        """Zapíše bajty na I2C sběrnici (podporuje joycar.i2c.I2C i surový busio.I2C)."""
        if hasattr(self._i2c, "__enter__"):
            with self._i2c:
                self._i2c.write(self._address, data)
        else:
            while not self._i2c.try_lock():
                pass
            try:
                self._i2c.writeto(self._address, data)
            finally:
                self._i2c.unlock()

    def writeRegister(self, reg: int, value: int) -> None:
        """Zapíše jeden bajt do zvoleného registru."""
        self._writeBytes(bytes([reg, value & 0xFF]))

    def initMotorDriver(self) -> None:
        """Inicializuje PCA9685: probudí oscilátor ze spánku a povolí auto-increment."""
        self.writeRegister(self.RegMODE1, self.RegMODE1_VALUE)

    def savePwm(self, value: int) -> tuple:
        """
        Přepočte hodnotu výkonu (0–4095) na zapínací a vypínací čítač (On, Off).

        Specialita PCA9685 (dle datasheetu NXP):
        - Při 100% sepnutí (plný plyn): nastaví bit LEDn_ON_FULL (hodnota 4096, 0).
        - Při 0% sepnutí (stop): nastaví bit LEDn_OFF_FULL (hodnota 0, 4096).
        - Pro běžné PWM vrací (0, value).
        """
        if value >= 4095:
            return 4096, 0   # Trvalé sepnutí na log. 1
        elif value <= 0:
            return 0, 4096   # Trvalé vypnutí na log. 0
        else:
            return 0, value  # Běžný PWM signál

    def writePwmToHbridge(self, channel: int, value: int) -> None:
        """
        Zapíše PWM výkon pro daný motor na dvojici kanálů (channel a channel+1).

        Args:
            channel (int): Základní kanál (0 pro pravý motor, 2 pro levý motor).
            value (int): Požadovaný výkon v rozsahu -4095 až +4095.
                         Kladná hodnota = vpřed (kanál channel)
                         Záporná hodnota = vzad (kanál channel+1)
        """
        if value > 0:
            val_on0, val_off0 = self.savePwm(value)
            val_on1, val_off1 = self.savePwm(0)
        else:
            val_on0, val_off0 = self.savePwm(0)
            val_on1, val_off1 = self.savePwm(-value)

        # Rychlý zápis všech 8 bajtů obou kanálů najednou
        data = bytearray([
            channel * 4 + self.RegPwm00,
            val_on0 & 0xFF, val_on0 >> 8, val_off0 & 0xFF, val_off0 >> 8,
            val_on1 & 0xFF, val_on1 >> 8, val_off1 & 0xFF, val_off1 >> 8,
        ])
        self._writeBytes(data)
