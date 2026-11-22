"""
sensors.py – Vyhodnocování senzorů robota JoyCar přes I2C expandér PCF8574.

Tento modul slouží jako vzorová implementace zpracování senzorických dat pro studenty.
Zajišťuje:
1. Periodické čtení digitálních vstupů z čipu PCF8574 po sběrnici I2C.
2. Invertování a maskování bitů (optické senzory čáry i překážek).
3. Podporu 2 až 6 senzorů čáry s možností snadného přepnutí (LineTracker2 .. 6).
4. Určení polohy robota vůči čáře (směrová odchylka od středu).
5. Detekci křižovatek (příčná čára, odbočka vlevo/vpravo).
6. Robustní detekci ztráty čáry s časovým filtrem (debounce timer).
7. Automatickou vizualizaci stavu senzorů na čelním LED displeji robota.

Hardware robota JoyCar:
-----------------------
- Všechny senzory jsou zapojeny na 8bitový I2C I/O expandér PCF8574 (adresa 0x38).
- Čárové senzory: 2 až 6 infračervených reflexních optočlenů na spodku podvozku.
- Překážkové senzory: 2 infračervené senzory směřující dopředu (vlevo a vpravo).
- V klidu (bílá plocha / bez překážky) jsou vstupy expandéru na log. 1.
- Při detekci černé čáry / překážky sepne fototranzistor k zemi (log. 0).
- Kód používá bitovou masku XOR k invertování logiky (1 = detekována čára).
"""

from typing import Optional
from joycar.pcf8574 import PCF8574
from joycar.line_trackers import BaseLineTracker, CrossRoadType, createLineTracker
from utils.period import Period
from utils.timer import Timer
from joycar.display import display


class LineSituationEnum:
    """Výčtový typ reprezentující celkovou situaci robota na trati."""
    LINE = 1
    CROSSROADS = 2


class Sensors:
    """
    Reprezentuje sadu senzorů robota JoyCar připojených přes expandér PCF8574.

    Podporuje jak standardní 3 tovární senzory, tak rozšíření na 2, 4, 5 nebo 6 senzorů.
    """

    # -------------------------------------------------------------------------
    # Bitové masky pro jednotlivé periferie na PCF8574:
    # -------------------------------------------------------------------------
    # Překážkové senzory (čelní IR sensory)
    ObstacleRight = 0x40  # Bit 6: Překážka vpravo
    ObstacleLeft  = 0x20  # Bit 5: Překážka vlevo

    # Čárové senzory (základní 3 vestavěné)
    LineRight  = 0x10     # Bit 4: Pravý senzor čáry
    LineMiddle = 0x08     # Bit 3: Střední senzor čáry
    LineLeft   = 0x04     # Bit 2: Levý senzor čáry

    # Rozšiřující piny pro 4, 5 a 6 senzorů
    LineFarLeft     = 0x01  # Bit 0 (EOUT0): Krajní levý senzor
    LineFarRight    = 0x02  # Bit 1 (EOUT1): Krajní pravý senzor
    LineMiddleRight = 0x80  # Bit 7 (EOUT7): Střední pravý senzor pro sudé počty
    LineMiddleLeft  = 0x08  # Bit 3: Střední levý senzor pro sudé počty

    # Výchozí maska 3 čárových senzorů pro operaci XOR (0x04 | 0x08 | 0x10 = 0x1C)
    LineAll = 0x1C

    # Maska pro detekci příčné křižovatky (současně levý i pravý senzor na čáře)
    LineCrossBoth = LineLeft | LineRight

    def __init__(self,
                 pcf8574: PCF8574,
                 lostLineTimeoutMs: int = 1000,
                 lineSensorCount: int = 3) -> None:
        """
        Inicializace subsystému senzorů.

        Args:
            pcf8574 (PCF8574): Ovladač I2C expandéru.
            lostLineTimeoutMs (int): Čas v ms pro toleranci krátkého výpadku čáry (debounce).
            lineSensorCount (int): Počet senzorů čáry (2, 3, 4, 5 nebo 6). Výchozí: 3.
        """
        self._pcf8574 = pcf8574
        self._periodRead = Period(timeout_ms=50)
        self._timerLostLine = Timer(timeout_ms=lostLineTimeoutMs, startTimer=False)

        # Nastavení strategie vyhodnocování čáry (2 až 6 senzorů)
        self._tracker: BaseLineTracker = createLineTracker(lineSensorCount)
        self._lineXorMask: int = self._tracker.xorMask

        self._data = -1
        self._dataPrev = -1

        # První okamžité načtení
        self.updateSensorData()

    @property
    def lineSensorCount(self) -> int:
        """Aktuálně nastavený počet senzorů čáry."""
        return self._tracker.sensorCount

    def setLineSensorCount(self, count: int) -> None:
        """
        Přepne konfiguraci počtu senzorů čáry (2, 3, 4, 5 nebo 6).
        """
        self._tracker = createLineTracker(count)
        self._lineXorMask = self._tracker.xorMask
        self.updateSensorData()

    # -------------------------------------------------------------------------
    # Nízkoúrovňová práce s I2C a bity
    # -------------------------------------------------------------------------

    def updateSensorData(self) -> None:
        """Přečte surová data z PCF8574 a invertuje bity aktivních čárových senzorů."""
        self._dataPrev = self._data
        raw = self._pcf8574.read()

        # Invertování čárových senzorů (0 = aktivní senzor na čáře)
        self._data = raw ^ self._lineXorMask

        if self._data != self._dataPrev:
            self._showOnDisplay()

    def _showOnDisplay(self) -> None:
        """Předá aktuální stav senzorů do bufferu čelního LED displeje."""
        count = self._tracker.sensorCount
        fl = self.areActive(self.LineFarLeft) if count >= 5 else None
        fr = self.areActive(self.LineFarRight) if count >= 5 else None

        if count in (4, 6):
            ml = self.areActive(self.LineMiddleLeft)
            mr = self.areActive(self.LineMiddleRight)
            m35 = None
        else:
            ml = None
            mr = None
            m35 = self.areActive(self.LineMiddle) if count >= 3 else None

        display.sensors(
            obstacleLeft   = self.isObstacleLeft(),
            farLeft        = fl,
            left           = self.areActive(self.LineLeft),
            midleLeft      = ml,
            midle35        = m35,
            midleRight     = mr,
            right          = self.areActive(self.LineRight),
            farRight       = fr,
            obstacleRight  = self.isObstacleRight(),
            bh = 9,
            bl = 1
        )

    def getSensorData(self, mask: int) -> int:
        """Vrátí vymaskovanou hodnotu z aktuálních dat senzorů."""
        return self._data & mask

    def areActive(self, sensorMask: int) -> bool:
        """Vrací True, pokud jsou VŠECHNY specifikované senzory v masce aktivní (bit = 0 po XORu)."""
        return self.getSensorData(sensorMask) == 0

    def isAnyActive(self, sensorMask: int) -> bool:
        """Vrací True, pokud je ALESPOŇ JEDEN ze senzorů v masce aktivní."""
        return self.getSensorData(sensorMask) != sensorMask

    # -------------------------------------------------------------------------
    # Pohodlné dotazy na stav jednotlivých senzorů
    # -------------------------------------------------------------------------

    def isLeftOnLine(self) -> bool:
        return self.areActive(Sensors.LineLeft)

    def isMiddleOnLine(self) -> bool:
        return self.areActive(Sensors.LineMiddle)

    def isRightOnLine(self) -> bool:
        return self.areActive(Sensors.LineRight)

    def isObstacleLeft(self) -> bool:
        return self.areActive(Sensors.ObstacleLeft)

    def isObstacleRight(self) -> bool:
        return self.areActive(Sensors.ObstacleRight)

    def isAnyObstacle(self) -> bool:
        return self.isObstacleLeft() or self.isObstacleRight()

    def hasAnyObstacle(self) -> bool:
        return self.isAnyObstacle()

    # -------------------------------------------------------------------------
    # Vysokoúrovňové metody pro sledování čáry a navigaci
    # -------------------------------------------------------------------------

    def getLineDirection(self) -> Optional[int]:
        """
        Vypočte směrovou odchylku robota od středu čáry.
        Deleguje na zvolenou strategii (LineTracker podle počtu senzorů).
        """
        return self._tracker.getLineDirection(self)

    def getTypeCrossRoads(self) -> int:
        """Určí typ detekované křižovatky (CrossRoadType.NONE, LEFT, RIGHT, CROSS)."""
        return self._tracker.getTypeCrossRoads(self)

    def isCrossRoads(self) -> bool:
        """Rychlý dotaz, zda je robot na křižovatce."""
        return self.getTypeCrossRoads() != CrossRoadType.NONE

    def getSituationLine(self) -> Optional[int]:
        """
        Vrátí celkovou situaci robota na trati (LineSituationEnum.LINE, CROSSROADS nebo None).
        Zahrnuje debounce časovač při ztrátě stopy.
        """
        if self.getTypeCrossRoads() == CrossRoadType.CROSS:
            self._timerLostLine.stopTimer()
            return LineSituationEnum.CROSSROADS

        direction = self.getLineDirection()
        if direction is not None:
            self._timerLostLine.stopTimer()
            return LineSituationEnum.LINE

        # Jsme mimo čáru – spustíme toleranční časovač
        if not self._timerLostLine.isStarted():
            self._timerLostLine.startTimer()

        if not self._timerLostLine.isTimeout():
            return LineSituationEnum.LINE

        return None

    def update(self) -> None:
        """Periodická aktualizace dat senzorů v hlavní smyčce (Superloop)."""
        if self._periodRead.isTime():
            self.updateSensorData()
