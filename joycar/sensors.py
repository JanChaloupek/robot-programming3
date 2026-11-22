"""
sensors.py – Vyhodnocování senzorů robota JoyCar přes I2C expandér PCF8574.

Tento modul slouží jako vzorová implementace zpracování senzorických dat pro studenty.
Zajišťuje:
1. Periodické čtení digitálních vstupů z čipu PCF8574 po sběrnici I2C.
2. Invertování a maskování bitů (optické senzory čáry i překážek).
3. Určení polohy robota vůči čáře (směrová odchylka -3 až +3 pro řízení motorů).
4. Detekci křižovatek (příčná čára, odbočka vlevo/vpravo).
5. Robustní detekci ztráty čáry s časovým filtrem (debounce timer), aby robot
   nezastavil při drobných nerovnostech nebo mezerách v lepicí pásce.
6. Automatickou vizualizaci stavu senzorů na čelním LED displeji robota.

Hardware robota JoyCar:
-----------------------
- Všechny senzory jsou zapojeny na 8bitový I2C I/O expandér PCF8574 (adresa 0x38).
- Čárové senzory: 3 infračervené reflexní optočleny na spodní straně podvozku.
- Překážkové senzory: 2 infračervené senzory směřující dopředu (vlevo a vpravo).
- V klidu (bílá plocha / bez překážky) jsou vstupy expandéru drženy na log. 1.
- Při detekci černé čáry / překážky sepne fototranzistor k zemi (log. 0).
- Kód proto používá bitovou masku XOR k invertování logiky, aby hodnota 1 znamenala
  "senzor je aktivní".
"""

from joycar.pcf8574 import PCF8574
from utils.period import Period
from utils.timer import Timer
from joycar.display import display


class LineSituationEnum:
    """
    Výčtový typ reprezentující celkovou situaci robota na trati.

    Slouží pro řídicí stavové automaty (State Machine):
    - LINE: Robot je bezpečně na čáře (nebo v tolerančním oknu krátkého výpadku).
    - CROSSROADS: Robot dorazil na křižovatku / příčnou čáru.
    """
    LINE = 1
    CROSSROADS = 2


class CrossRoadType:
    """
    Klasifikace typu detekované křižovatky podle aktivovaných senzorů.

    Hodnoty:
    - NONE (0): Žádná křižovatka (běžná čára nebo prázdno).
    - LEFT (1): Odbočka vlevo (čára pod levým a středním senzorem současně).
    - RIGHT (2): Odbočka vpravo (čára pod pravým a středním senzorem současně).
    - CROSS (3): Křížení / T-křižovatka / stop čára (levý i pravý senzor vidí čáru).
    """
    NONE = 0
    LEFT = 1
    RIGHT = 2
    CROSS = 3


class Sensors:
    """
    Reprezentuje sadu senzorů robota JoyCar připojených přes expandér PCF8574.

    Třída poskytuje nízkoúrovňové metody pro testování jednotlivých bitů (areActive),
    i vysokoúrovňové metody pro navigaci (getLineDirection, getSituationLine).
    """

    # -------------------------------------------------------------------------
    # Bitové masky pro jednotlivé periferie na PCF8574:
    # -------------------------------------------------------------------------
    # Překážkové senzory (čelní IR sensory)
    ObstacleRight = 0x40  # Bit 6: Překážka vpravo
    ObstacleLeft  = 0x20  # Bit 5: Překážka vlevo

    # Čárové senzory (spodní IR reflexní sensory)
    LineRight  = 0x10     # Bit 4: Pravý senzor čáry
    LineMiddle = 0x08     # Bit 3: Střední senzor čáry
    LineLeft   = 0x04     # Bit 2: Levý senzor čáry

    # Maska všech čárových senzorů pro operaci XOR (0x04 | 0x08 | 0x10 = 0x1C)
    LineAll = 0x1C

    # Maska pro detekci příčné křižovatky (současně levý i pravý senzor na čáře)
    LineCrossBoth = LineLeft | LineRight

    def __init__(self, pcf8574: PCF8574, lostLineTimeoutMs: int = 1000) -> None:
        """
        Inicializace subsystému senzorů.

        Args:
            pcf8574 (PCF8574): Ovladač I2C expandéru.
            lostLineTimeoutMs (int): Čas v milisekundách, po který robot toleruje
                ztrátu čáry (např. přejezd spáry či bílého místa), než nahlásí,
                že se definitivně ztratil. Výchozí hodnota je 1000 ms.
        """
        self._pcf8574 = pcf8574

        # Perioda pro čtení senzorů (50 ms odpovídá frekvenci 20 Hz, což bohatě
        # stačí pro stabilitu řízení a nezahlcuje I2C sběrnici).
        self._periodRead = Period(timeout_ms=50)

        # Časovač pro toleranci výpadku čáry (debounce při ztrátě stopy)
        self._timerLostLine = Timer(timeout_ms=lostLineTimeoutMs, startTimer=False)

        # Vyrovnávací paměť posledních načtených dat
        self._data = -1
        self._dataPrev = -1

        # Provedeme první okamžité načtení
        self.updateSensorData()

    # -------------------------------------------------------------------------
    # Nízkoúrovňová práce s I2C a bity
    # -------------------------------------------------------------------------

    def updateSensorData(self) -> None:
        """
        Přečte surová data z PCF8574, invertuje logiku čárových senzorů
        a při změně stavu aktualizuje zobrazení na displeji.

        Vysvětlení pro studenty:
            Optočleny na černé čáře vrací logickou 0. Pro snadnější práci
            v kódu chceme mít 1 = detekována čára. Proto aplikujeme operaci
            XOR s maskou LineAll (0x1C):
            vstup 0 ^ 1 = 1 (čára aktivní)
            vstup 1 ^ 1 = 0 (bílá podložka, neaktivní)
        """
        self._dataPrev = self._data
        raw = self._pcf8574.read()

        # Invertování čárových senzorů
        self._data = raw ^ Sensors.LineAll

        # Pokud se stav senzorů změnil, překreslíme ikonu na displeji
        if self._data != self._dataPrev:
            self._showOnDisplay()

    def _showOnDisplay(self) -> None:
        """
        Předá aktuální stav všech senzorů do bufferu displeje.
        Poznámka: Skutečné fyzické rozsvícení LED provede display.updatePixels()
        v hlavní smyčce.
        """
        display.sensors(
            obstacleLeft   = self.isObstacleLeft(),
            farLeft        = None,
            left           = self.areActive(Sensors.LineLeft),
            midleLeft      = None,
            midle35        = self.areActive(Sensors.LineMiddle),
            midleRight     = None,
            right          = self.areActive(Sensors.LineRight),
            farRight       = None,
            obstacleRight  = self.isObstacleRight(),
            bh = 9,
            bl = 1
        )

    def getSensorData(self, mask: int) -> int:
        """Vrátí vymaskovanou hodnotu z aktuálních dat senzorů."""
        return self._data & mask

    def areActive(self, sensorMask: int) -> bool:
        """
        Ověří, zda jsou VŠECHNY bity v zadané masce aktivní (rovny 0 v interním registru).

        Příklad:
            areActive(Sensors.LineLeft | Sensors.LineRight) -> True pouze tehdy,
            když oba krajní senzory současně vidí čáru.
        """
        return self.getSensorData(sensorMask) == 0

    def isAnyActive(self, sensorMask: int) -> bool:
        """
        Ověří, zda je ALESPOŇ JEDEN senzor ze zadané masky aktivní.

        Příklad:
            isAnyActive(Sensors.ObstacleLeft | Sensors.ObstacleRight) -> True
            pokud je před robotem jakákoli překážka.
        """
        return self.getSensorData(sensorMask) != sensorMask

    # -------------------------------------------------------------------------
    # Čelní překážkové senzory
    # -------------------------------------------------------------------------

    def isObstacleLeft(self) -> bool:
        """Vrací True, pokud levý senzor detekuje překážku."""
        return self.areActive(Sensors.ObstacleLeft)

    def isObstacleRight(self) -> bool:
        """Vrací True, pokud pravý senzor detekuje překážku."""
        return self.areActive(Sensors.ObstacleRight)

    def isAnyObstacle(self) -> bool:
        """Vrací True, pokud je detekována překážka vlevo nebo vpravo."""
        return self.isAnyActive(Sensors.ObstacleLeft | Sensors.ObstacleRight)

    # -------------------------------------------------------------------------
    # Vysokoúrovňová navigace po čáře (Line Following)
    # -------------------------------------------------------------------------

    def getTypeCrossRoads(self) -> int:
        """
        Analyzuje geometrii čáry a detekuje křižovatku.

        Princip pro studenty:
        - Běžná sledovaná čára má šířku cca 15–20 mm, takže ji obvykle vidí
          buď 1 nebo maximálně 2 sousední senzory.
        - Pokud jsou aktivní LEVÝ i PRAVÝ senzor zároveň, robot narazil na
          kolmou čáru (křížení nebo T-křižovatka).

        Returns:
            CrossRoadType.CROSS (3) při kolmé čáře / plné křižovatce,
            CrossRoadType.LEFT (1) při větvení doleva,
            CrossRoadType.RIGHT (2) při větvení doprava,
            CrossRoadType.NONE (0) na běžném přímém úseku nebo zatáčce.
        """
        left = self.areActive(Sensors.LineLeft)
        right = self.areActive(Sensors.LineRight)
        middle = self.areActive(Sensors.LineMiddle)

        if left and right:
            return CrossRoadType.CROSS
        if left and middle:
            return CrossRoadType.LEFT
        if right and middle:
            return CrossRoadType.RIGHT
        return CrossRoadType.NONE

    def getLineDirection(self) -> int | None:
        """
        Vypočte směrovou odchylku robota od středu čáry.

        Tato hodnota slouží přímo jako vstup pro proporcionální řízení motorů:
        - Kladná hodnota znamená, že čára je vlevo -> robot musí zatočit doleva.
        - Záporná hodnota znamená, že čára je vpravo -> robot musí zatočit doprava.
        - Čím vyšší absolutní hodnota, tím prudší korekce je vyžadována.

        Stupnice:
          None : Robot je mimo čáru (žádný senzor nevidí čáru), nebo je na křižovatce.
             0 : Perfektní stopa – čára je přesně pod středním senzorem.
            +1 : Mírná odchylka vlevo – čára je mezi středním a levým senzorem.
            +3 : Velká odchylka vlevo – čára je pouze pod levým senzorem (je nutné prudce točit).
            -1 : Mírná odchylka vpravo – čára je mezi středním a pravým senzorem.
            -3 : Velká odchylka vpravo – čára je pouze pod pravým senzorem.

        Returns:
            int (-3 až +3) nebo None.
        """
        left = self.areActive(Sensors.LineLeft)
        right = self.areActive(Sensors.LineRight)
        middle = self.areActive(Sensors.LineMiddle)

        # Pokud vidíme levý i pravý zároveň, jde o křižovatku, nikoli o běžný směr
        if left and right:
            return None

        # Pokud žádný senzor nevidí černou, jsme mimo trať
        if not left and not right and not middle:
            return None

        # Čára je přesně uprostřed
        if middle and not left and not right:
            return 0

        # Mírné odchylky (čára je na rozhraní dvou senzorů)
        if middle and left:
            return 1
        if middle and right:
            return -1

        # Výrazné odchylky (střední senzor čáru ztratil, drží ji jen krajní)
        if left:
            return 3
        if right:
            return -3

        return None

    def getSituationLine(self) -> int | None:
        """
        Vyhodnotí celkový stav jízdy po čáře s filtrem falešné ztráty stopy.

        Princip debounce filtru:
            V reálném světě může lepicí páska obsahovat drobné mezery, odlesky
            nebo robot při rychlém přejezdu nadskočí. Kdybychom reagovali okamžitě,
            robot by při sebemenším výpadku nouzově zastavil.
            Proto při ztrátě stopy nastartujeme časovač `_timerLostLine`.
            Dokud nevyprší limit (např. 1000 ms), robot předstírá, že je stále
            na čáře, a pokračuje v posledním manévru. Teprve po vypršení časovače
            vrátí None (robot je definitivně ztracen a zastaví).

        Returns:
            LineSituationEnum.CROSSROADS : Robot stojí na křižovatce.
            LineSituationEnum.LINE       : Robot jede po čáře (nebo v toleranci).
            None                         : Robot ztratil čáru na dobu delší než timeout.
        """
        # 1. Kontrola křižovatky (má nejvyšší prioritu)
        if self.getTypeCrossRoads() == CrossRoadType.CROSS:
            self._timerLostLine.stopTimer()
            return LineSituationEnum.CROSSROADS

        # 2. Běžná jízda po čáře
        if self.getLineDirection() is not None:
            self._timerLostLine.stopTimer()
            return LineSituationEnum.LINE

        # 3. Ztráta čáry – začínáme odpočítávat toleranční čas
        if not self._timerLostLine.isStarted():
            self._timerLostLine.startTimer()

        # Dokud nevypršel timeout, tvrdíme stav LINE
        if not self._timerLostLine.isTimeout():
            return LineSituationEnum.LINE

        # Timeout vypršel – robot se skutečně ztratil
        return None

    def update(self) -> None:
        """Periodická aktualizace – volá se v hlavní smyčce robota."""
        if self._periodRead.isTime():
            self.updateSensorData()
