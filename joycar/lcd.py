"""
lcd.py – Ovladač alfanumerického textového LCD displeje pro JoyCar robota.

Tento modul poskytuje třídu TextDisplay pro řízení znakových LCD displejů
(např. 16×2 nebo 20×4 znaků s řadičem HD44780) připojených přes I2C převodník PCF8574.

Výukový kontext pro studenty:
-----------------------------
1. Řadič displeje HD44780 komunikuje v tzv. 4bitovém režimu (data se posílají po dvou půlbajtech / nibblech).
2. Převodník PCF8574 mapuje bity z I2C sběrnice na piny displeje:
   - Bit P0: RS (Register Select – 0 pro příkazy, 1 pro textová data).
   - Bit P1: RW (Read/Write – trvale 0 pro zápis).
   - Bit P2: E  (Enable – náběžná a sestupná hrana pro zapamatování dat).
   - Bit P3: Podsvícení (Backlight – 1 = rozsvíceno, 0 = zhasnuto).
   - Bity P4–P7: Datové bity D4–D7.

Klíčová vlastnost: Displej lze jednoduše zapínat a vypínat (enable/disable).
Pokud je vypnutý (nebo není fyzicky připojen), nezatěžuje I2C sběrnici a kód robota běží dál.
"""

import time
from typing import Optional, Any
from utils.log import log

# Masky řídicích signálů převodníku PCF8574:
_MASK_RS = 0x01          # P0: Register Select (0=příkaz, 1=data)
_MASK_RW = 0x02          # P1: Read/Write
_MASK_E  = 0x04          # P2: Enable strobe
_SHIFT_BACKLIGHT = 3     # P3: Podsvícení
_SHIFT_DATA = 4          # P4–P7: 4bitová data

# Významné příkazy řadiče HD44780:
_CMD_CLEAR_DISPLAY = 0x01
_CMD_RETURN_HOME   = 0x02
_CMD_ENTRY_MODE    = 0x04
_CMD_DISPLAY_CTRL  = 0x08
_CMD_CURSOR_SHIFT  = 0x10
_CMD_FUNCTION_SET  = 0x20
_CMD_SET_CGRAM_ADDR = 0x40
_CMD_SET_DDRAM_ADDR = 0x80

# Příznaky pro řízení zobrazení:
_FLAG_DISPLAY_ON   = 0x04
_FLAG_CURSOR_ON    = 0x02
_FLAG_BLINK_ON     = 0x01

# Příznaky pro inicializaci:
_FLAG_2_LINE       = 0x08
_FLAG_5x8_DOTS     = 0x00


class TextDisplay:
    """
    Ovladač textového LCD displeje přes I2C pro robot JoyCar.

    Umožňuje:
    - zobrazovat textové zprávy, čísla a ladicí výpisy,
    - zobrazovat souřadnice odometrie (x, y, theta),
    - snadné zapnutí / vypnutí (aby nebrzdil hlavní smyčku, pokud není potřeba),
    - samostatné ovládání podsvícení.
    """

    def __init__(self,
                 i2c: Any,
                 address: int = 0x27,
                 rows: int = 4,
                 cols: int = 20,
                 enabled: bool = True) -> None:
        """
        Inicializace textového LCD displeje.

        Args:
            i2c (Any): I2C sběrnice.
            address (int): I2C adresa převodníku PCF8574 (typicky 0x27 nebo 0x3F).
            rows (int): Počet řádků (typicky 2 nebo 4).
            cols (int): Počet sloupců (typicky 16 nebo 20).
            enabled (bool): Výchozí stav displeje (zapnutý / vypnutý).
        """
        self._i2c = i2c
        self._address = address
        self._rows = rows
        self._cols = cols
        self._enabled = enabled
        self._backlight = True
        self._cursorCol = 0
        self._cursorRow = 0
        self._hardwarePresent = False

        if self._enabled:
            self._initHardware()

    # -------------------------------------------------------------------------
    # Zapínání a vypínání displeje
    # -------------------------------------------------------------------------

    @property
    def is_enabled(self) -> bool:
        """Vrací True, pokud je displej aktivní a připraven k zápisu."""
        return self._enabled and self._hardwarePresent

    def enable(self) -> None:
        """Zapne displej a aktivuje odesílání dat na I2C sběrnici."""
        if not self._enabled:
            self._enabled = True
            if not self._hardwarePresent:
                self._initHardware()
            self.backlight_on()
            log.info("TextDisplay: zapnut.")

    def disable(self) -> None:
        """Vypne displej, zhasne podsvícení a pozastaví komunikaci na I2C."""
        if self._enabled:
            if self._hardwarePresent:
                self.backlight_off()
            self._enabled = False
            log.info("TextDisplay: vypnut.")

    def backlight_on(self) -> None:
        """Rozsvítí podsvícení displeje."""
        self._backlight = True
        if self._hardwarePresent:
            self._writeRaw(0)

    def backlight_off(self) -> None:
        """Zhasne podsvícení displeje."""
        self._backlight = False
        if self._hardwarePresent:
            self._writeRaw(0)

    # -------------------------------------------------------------------------
    # Uživatelské metody pro výpis textu
    # -------------------------------------------------------------------------

    def clear(self) -> None:
        """Smaže celý displej a vrátí kurzor do levého horního rohu (0, 0)."""
        if not self.is_enabled:
            return
        self._sendCommand(_CMD_CLEAR_DISPLAY)
        time.sleep(0.003)  # Příkaz Clear vyžaduje delší čas na provedení (min. 1.6 ms)
        self._cursorCol = 0
        self._cursorRow = 0

    def move_to(self, col: int, row: int) -> None:
        """Přesune textový kurzor na zadaný sloupec (0 až cols-1) a řádek (0 až rows-1)."""
        if not self.is_enabled:
            return
        self._cursorCol = max(0, min(self._cols - 1, col))
        self._cursorRow = max(0, min(self._rows - 1, row))

        # Výpočet DDRAM adresy v paměti řadiče HD44780
        row_offsets = [0x00, 0x40, 0x14, 0x54]
        addr = self._cursorCol + row_offsets[self._cursorRow % 4]
        self._sendCommand(_CMD_SET_DDRAM_ADDR | addr)

    def write(self, text: str) -> None:
        """Vypíše zadaný text od aktuální pozice kurzoru."""
        if not self.is_enabled:
            return
        for char in text:
            if char == '\n':
                self._cursorRow = (self._cursorRow + 1) % self._rows
                self._cursorCol = 0
                self.move_to(self._cursorCol, self._cursorRow)
            else:
                self._sendData(ord(char))
                self._cursorCol += 1
                if self._cursorCol >= self._cols:
                    self._cursorCol = 0
                    self._cursorRow = (self._cursorRow + 1) % self._rows
                    self.move_to(self._cursorCol, self._cursorRow)

    def putstr(self, text: str) -> None:
        """Alias pro write() pro kompatibilitu se starším kódem z 2-SW_GIT."""
        self.write(text)

    def writeLine(self, row: int, text: str) -> None:
        """
        Vypíše text na daný řádek a zbytek řádku automaticky doplní mezerami
        (zabrání zobrazení starých nechtěných znaků).
        """
        if not self.is_enabled:
            return
        # Ořízneme nebo doplníme text přesně na délku řádku
        padded = text[:self._cols].ljust(self._cols)
        self.move_to(0, row)
        self.write(padded)

    def writePosition(self, x: float, y: float, theta: float) -> None:
        """
        Výuková obrazovka odometrie:
        Zobrazí aktuální souřadnice robota v základních SI jednotkách:
        x, y v metrech [m], theta v radiánech [rad].
        """
        if not self.is_enabled:
            return
        self.writeLine(0, "   Pozice JoyCaru")
        self.writeLine(1, f" X: {x:6.3f} m")
        self.writeLine(2, f" Y: {y:6.3f} m")
        self.writeLine(3, f" T: {theta:6.3f} rad")

    # -------------------------------------------------------------------------
    # Nízkoúrovňová komunikace s HD44780 ve 4bitovém režimu
    # -------------------------------------------------------------------------

    def _writeRaw(self, byte_val: int) -> bool:
        """Zapíše jeden bajt přímo do expandéru PCF8574 po I2C."""
        backlight_bit = (1 << _SHIFT_BACKLIGHT) if self._backlight else 0
        payload = bytearray([byte_val | backlight_bit])

        try:
            if hasattr(self._i2c, "__enter__"):
                with self._i2c:
                    self._i2c.write(self._address, payload)
                return True
            else:
                while not self._i2c.try_lock():
                    pass
                try:
                    self._i2c.writeto(self._address, payload)
                    return True
                finally:
                    self._i2c.unlock()
        except Exception as e:
            log.debug(f"TextDisplay: Zápis na I2C selhal: {e}")
            return False

    def _pulseEnable(self, nibble_with_control: int) -> None:
        """Vygeneruje náběžnou a sestupnou hranu na pinu E (strobe signál)."""
        self._writeRaw(nibble_with_control | _MASK_E)   # E = 1
        time.sleep(0.0001)                              # Krátký pulz (100 us)
        self._writeRaw(nibble_with_control & ~_MASK_E)  # E = 0
        time.sleep(0.0001)

    def _sendNibble(self, nibble: int, is_data: bool = False) -> None:
        """Odešle 4 bity (horní nibble) s příslušným nastavením RS."""
        rs_bit = _MASK_RS if is_data else 0
        control_byte = ((nibble & 0x0F) << _SHIFT_DATA) | rs_bit
        self._pulseEnable(control_byte)

    def _sendByte(self, byte_val: int, is_data: bool = False) -> None:
        """Odešle plný 8bitový bajt rozdělený na horní a dolní nibble."""
        self._sendNibble((byte_val >> 4) & 0x0F, is_data=is_data)
        self._sendNibble(byte_val & 0x0F, is_data=is_data)

    def _sendCommand(self, cmd: int) -> None:
        """Odešle řídicí příkaz do řadiče displeje (RS = 0)."""
        self._sendByte(cmd, is_data=False)

    def _sendData(self, data: int) -> None:
        """Odešle znaková data do paměti DDRAM displeje (RS = 1)."""
        self._sendByte(data, is_data=True)

    def _initHardware(self) -> None:
        """Inicializační sekvence řadiče HD44780 pro přechod do 4bitového režimu."""
        # 1. Test přítomnosti zařízení na I2C sběrnici
        if not self._writeRaw(0):
            log.info(f"TextDisplay: Displej na I2C adrese 0x{self._address:02X} nenalezen, zůstává neaktivní.")
            self._hardwarePresent = False
            return

        self._hardwarePresent = True
        time.sleep(0.05)  # Čekání min. 40 ms po zapnutí napájení

        # 2. Resetovací sekvence (3x poslání 0x03 dle datasheetu)
        self._sendNibble(0x03)
        time.sleep(0.005)
        self._sendNibble(0x03)
        time.sleep(0.001)
        self._sendNibble(0x03)
        time.sleep(0.001)

        # 3. Přepnutí do 4bitového režimu
        self._sendNibble(0x02)
        time.sleep(0.001)

        # 4. Nastavení parametrů: 2 řádky, matice 5x8 bodů
        self._sendCommand(_CMD_FUNCTION_SET | _FLAG_2_LINE | _FLAG_5x8_DOTS)

        # 5. Zapnutí displeje bez blikajícího kurzoru
        self._sendCommand(_CMD_DISPLAY_CTRL | _FLAG_DISPLAY_ON)

        # 6. Vymazání displeje a nastavení směru posuvu textu doprava
        self.clear()
        self._sendCommand(_CMD_ENTRY_MODE | 0x02)

        log.info(f"TextDisplay: Inicializován ({self._cols}x{self._rows} na adrese 0x{self._address:02X}).")
