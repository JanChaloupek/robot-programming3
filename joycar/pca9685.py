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


class PCA9685_registers:
    """
    Adresy registrů a řídicí konstanty čipu PCA9685.

    Podobně jako PCA9633_registers poskytuje symbolické konstanty
    pro přehlednou a výukově srozumitelnou práci s I2C registry.
    """
    MODE1 = 0x00         # Řídicí registr režimu 1 (řízení spánku a auto-incrementu)
    MODE1_VALUE = 0x20   # Běžný provoz s povoleným auto-incrementem adres registrů
    MODE2 = 0x01         # Řídicí registr režimu 2
    SUBADR1 = 0x02       # I2C subadresa 1
    SUBADR2 = 0x03       # I2C subadresa 2
    SUBADR3 = 0x04       # I2C subadresa 3
    ALLCALLADR = 0x05    # AllCall I2C adresa

    # Registry pro kanál 0 (ON_L, ON_H, OFF_L, OFF_H)
    LED0_ON_L = 0x06
    LED0_ON_H = 0x07
    LED0_OFF_L = 0x08
    LED0_OFF_H = 0x09
    PWM00 = 0x06         # Alias pro začátek registrů kanálu 0

    ALL_LED_ON_L = 0xFA  # Hromadné nastavení všech kanálů
    ALL_LED_ON_H = 0xFB
    ALL_LED_OFF_L = 0xFC
    ALL_LED_OFF_H = 0xFD
    PRE_SCALE = 0xFE     # Nastavení předděličky pro frekvenci PWM


class PCA9685:
    """Ovladač I2C PWM generátoru PCA9685 pro řízení motorů JoyCaru."""

    MAX_PWM = 4095

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
        self.writeRegister(PCA9685_registers.MODE1, PCA9685_registers.MODE1_VALUE)

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
            channel * 4 + PCA9685_registers.PWM00,
            val_on0 & 0xFF, val_on0 >> 8, val_off0 & 0xFF, val_off0 >> 8,
            val_on1 & 0xFF, val_on1 >> 8, val_off1 & 0xFF, val_off1 >> 8,
        ])
        self._writeBytes(data)
