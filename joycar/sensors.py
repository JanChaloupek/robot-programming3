"""
sensors.py – čtení senzorů JoyCar robota přes PCF8574.

Tento modul poskytuje třídu Sensors, která:
- periodicky čte data z PCF8574,
- interpretuje jednotlivé bity jako senzory,
- předává stav senzorů metodě Display.senzors().

POZOR:
    Display.senzors() pouze zapisuje do bufferu displeje.
    Aby se změny skutečně zobrazily, je nutné pravidelně volat:

        Display.updatePixels()

    typicky v hlavní smyčce robota.
"""

from joycar.pcf8574 import PCF8574
from utils.period import Period
from joycar.display import Display


class Sensors:
    """Reprezentuje sadu senzorů robota připojených přes PCF8574."""

    # Bity z PCF8574
    ObstacleRight = 0x40
    ObstacleLeft  = 0x20

    LineRight  = 0x10
    LineMiddle = 0x08
    LineLeft   = 0x04

    # maska pro invertování čárových senzorů
    LineAll = 0x1C

    def __init__(self, pcf8574: PCF8574) -> None:
        self._pcf8574 = pcf8574
        self._periodRead = Period(timeout_ms=50)
        self._data = -1
        self.updateSensorData()

    # ---------------------------------------------------------
    # Čtení dat
    # ---------------------------------------------------------

    def updateSensorData(self) -> None:
        """
        Přečte data ze senzorů a aktualizuje stav.

        Pokud se stav změnil, zavolá Display.senzors().
        """
        self._dataPrev = self._data
        raw = self._pcf8574.read()

        # invertování čárových senzorů (0 = aktivní)
        self._data = raw ^ Sensors.LineAll

        if self._data != self._dataPrev:
            self._showOnDisplay()

    def _showOnDisplay(self) -> None:
        """
        Předá stav senzorů metodě Display.senzors().

        Display.senzors() pouze zapisuje do bufferu.
        Pro skutečné vykreslení je nutné volat Display.updatePixels().
        """
        Display.senzors(
            obstacleLeft   = self.areActive(Sensors.ObstacleLeft),
            farLeft        = None,
            left           = self.areActive(Sensors.LineLeft),
            midleLeft      = None,
            midle35        = self.areActive(Sensors.LineMiddle),
            midleRight     = None,
            right          = self.areActive(Sensors.LineRight),
            farRight       = None,
            obstacleRight  = self.areActive(Sensors.ObstacleRight),
            bh = 9,
            bl = 1
        )

    # ---------------------------------------------------------
    # API pro logiku robota
    # ---------------------------------------------------------

    def getSensorData(self, mask: int) -> int:
        """Vrátí hodnotu bitů podle masky."""
        return self._data & mask

    def areActive(self, sensor: int) -> bool:
        """Vrátí True pokud jsou všechny bity senzoru aktivní (0)."""
        return self.getSensorData(sensor) == 0

    def isAnyActive(self, sensor: int) -> bool:
        """Vrátí True pokud je alespoň jeden bit senzoru aktivní."""
        return self.getSensorData(sensor) != sensor

    def update(self) -> None:
        """
        Periodicky aktualizuje stav senzorů.

        POZOR:
            Display.senzors() pouze zapisuje do bufferu.
            Překreslení provádí Display.updatePixels().
        """
        if self._periodRead.isTime():
            self.updateSensorData()
