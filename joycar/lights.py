"""
lights.py – Řízení světel a blinkrů robota JoyCar (NeoPixel WS2812B).

Vzorový výukový modul pro studenty:
-----------------------------------
Tento modul ukazuje, jak na robotovi realizovat kompletní automobilové osvětlení:
- potkávací a dálková přední světla
- zadní obrysová světla
- automatická brzdová světla při zpomalení nebo zastavení
- couvací světlo při zařazení zpátečky
- neblokující blinkry a výstražná světla

Doporučené studijní materiály (repozitář pomůcek):
- file:///C:/Projekty/pomucky/superloop.md – Princip neblokujícího blikání pomocí objektu Timer/Period
- file:///C:/Projekty/pomucky/sleep.md – Proč v obsluze světel nikdy nesmíme volat sleep()

Hardware robota JoyCar:
-----------------------
Podvozek je vybaven páskem 8 adresovatelných RGB LED (typ WS2812B / NeoPixel)
připojeným na digitální pin P0. Každá LED má v řetězci svůj pevný index (0 až 7):

     [0: Přední L světlo]      [3: Přední P světlo]
     [1: Přední L blinkr]      [2: Přední P blinkr]
              |                         |
              |     PODVOZEK JOYCAR     |
              |                         |
     [4: Zadní L blinkr ]      [7: Zadní P blinkr ]
     [5: Zadní L světlo ]      [6: Zadní P světlo ]
       (brzda / zpátečka)        (brzda)

Barevný model RGB:
------------------
Barva je reprezentována trojicí celých čísel (červená, zelená, modrá) v rozsahu 0–255.
Příklady:
- (0, 0, 0)       = zhasnuto
- (100, 35, 0)    = typická oranžová pro blinkry
- (60, 60, 60)    = tlumená bílá (potkávací světla)
- (255, 255, 255) = plný jas bílé (dálková světla)
- (60, 0, 0)      = tlumená červená (zadní obrysová světla)
- (255, 0, 0)     = plný svit červené (brzdová světla)
"""

import board
from neopixel import NeoPixel
from utils.period import Period
from utils.timer import Timer
from joycar.direction import DirectionEnum


class BeamsEnum:
    """Režimy předních světlometů robota."""
    OFF = 0       # Zhasnuto
    DIPPED = 1    # Potkávací světla (tlumený svit)
    HIGH = 2      # Dálková světla (plný svit)


class Indicator:
    """
    Logický generátor signálu pro směrová (blinkry) a výstražná světla.

    Tato třída neprovádí samotné rozsvěcování LED diod, ale v neblokujících
    intervalech (výchozích 400 ms) počítá stav: svítí / nesvítí.
    """

    def __init__(self, blinkIntervalMs: int = 400) -> None:
        """
        Args:
            blinkIntervalMs (int): Doba trvání jednoho pulzu (zapnuto/vypnuto) v ms.
        """
        self.direction = None
        self.warning = False
        self._period = Period(timeout_ms=blinkIntervalMs)
        self.indicatorLight = None  # None = vypnuto, True = svítí, False = mezera

    def isLeft(self) -> bool:
        """Vrací True, pokud má blikat levá strana (včetně výstražných světel)."""
        return self.warning or (self.direction in (DirectionEnum.LEFT, 1, "LEFT", "left"))

    def isRight(self) -> bool:
        """Vrací True, pokud má blikat pravá strana (včetně výstražných světel)."""
        return self.warning or (self.direction in (DirectionEnum.RIGHT, 2, "RIGHT", "right"))

    def update(self) -> None:
        """
        Periodická aktualizace stavu blinkru.
        Volá se v každém průchodu hlavní smyčky bez blokování.
        """
        if self.isLeft() or self.isRight():
            if self.indicatorLight is None:
                # Zahájení blikání – okamžitě rozsvítíme a spustíme časovač
                self.indicatorLight = True
                self._period.startTimer()
        else:
            # Blinkr byl vypnut
            self.indicatorLight = None
            self._period.stopTimer()

        # Pokud blinkr běží, přepínáme stav při každém vypršení periody
        if self.indicatorLight is not None and self._period.isTime():
            self.indicatorLight = not self.indicatorLight


class LightsControl:
    """
    Kompletní subsystém pro ovládání všech světel na robotovi JoyCar.

    Zajišťuje:
    - přepínání potkávacích / dálkových světel
    - automatické rozsvícení brzdových světel při snížení rychlosti (s timeoutem 600 ms)
    - bílé couvací světlo při jízdě vzad
    - blikání oranžových LED na příslušné straně (či výstražných na obou)
    """

    # Definice barevných konstant (R, G, B)
    COLOR_OFF           = (0, 0, 0)
    COLOR_ORANGE        = (100, 35, 0)
    COLOR_WHITE_DIPPED  = (60, 60, 60)
    COLOR_WHITE_HIGH    = (255, 255, 255)
    COLOR_RED_TAIL      = (60, 0, 0)
    COLOR_RED_BRAKE     = (255, 0, 0)
    COLOR_WHITE_REVERSE = (60, 60, 60)

    # Indexy LED diod na 8prvkovém pásku JoyCar
    IND_LEFT        = (1, 4)  # Levý přední a zadní blinkr
    IND_RIGHT       = (2, 7)  # Pravý přední a zadní blinkr
    HEAD_LIGHTS     = (0, 3)  # Přední světlomety
    BACK_LIGHTS     = (5, 6)  # Zadní obrysová a brzdová světla
    REVERSE_LIGHTS  = (5,)    # Levé zadní světlo přepínané na bílou při couvání

    def __init__(
        self,
        pin=board.P0,
        num_pixels: int = 8,
        neopixel_instance: NeoPixel = None,
        brakeTimeoutMs: int = 600
    ) -> None:
        """
        Inicializace světelného subsystému.

        Args:
            pin: Fyzický pin Pico:ed, na kterém je připojen NeoPixel (výchozí P0).
            num_pixels (int): Počet diod v pásku (pro JoyCar je to 8).
            neopixel_instance (NeoPixel|None): Možnost předat již vytvořenou instanci (pro testy).
            brakeTimeoutMs (int): Doba v ms, po kterou zůstanou svítit brzdová světla po zastavení.
        """
        if neopixel_instance is not None:
            self._pixels = neopixel_instance
        else:
            self._pixels = NeoPixel(pin, num_pixels, auto_write=False)

        self.mainBeams = BeamsEnum.OFF
        self.indicator = Indicator()

        self._oldForward = 0.0
        self._currentForward = 0.0
        self._brakeTimer = Timer(timeout_ms=brakeTimeoutMs, startTimer=False)

        # Perioda pro vykreslování na LED (50 ms = 20 Hz, šetří čas procesoru)
        self._showPeriod = Period(timeout_ms=50)
        # Nastavíme počáteční čas do minulosti, aby první volání update() okamžitě vykreslilo barvy
        self._showPeriod.startTimer(start_time_ms=-100)

    # -------------------------------------------------------------------------
    # Reakce na pohyb a brzdění
    # -------------------------------------------------------------------------

    def setForwardSpeed(self, forwardSpeed: float) -> None:
        """
        Nastaví aktuální dopřednou rychlost pro výpočet brzdových a zpětných světel.
        Kladná hodnota = jízda vpřed, záporná hodnota = couvání, 0 = stojíme.
        """
        # Detekce brzdění: pokud jsme jeli dopředu a nyní stojíme nebo couváme
        if self._currentForward > 0.0 and forwardSpeed <= 0.0:
            self._brakeTimer.startTimer()

        self._oldForward = self._currentForward
        self._currentForward = forwardSpeed

    def isBraking(self) -> bool:
        """Vrací True, pokud má aktivně svítit brzdové světlo."""
        if self._brakeTimer.isStarted():
            if not self._brakeTimer.isTimeout():
                return True
            self._brakeTimer.stopTimer()
        return False

    def isReversing(self) -> bool:
        """Vrací True, pokud robot couvá."""
        return self._currentForward < 0.0

    # -------------------------------------------------------------------------
    # Vykreslování a míchání barev
    # -------------------------------------------------------------------------

    def _setLedGroup(self, indices: tuple, color: tuple) -> None:
        """Nastaví barvu pro vybranou skupinu LED diod."""
        for idx in indices:
            if idx < len(self._pixels):
                self._pixels[idx] = color

    def _updateColors(self) -> None:
        """Vypočte a zapíše barvy pro všechny LED na základě aktuálního stavu."""
        # 1. Přední světla (potkávací / dálková / vypnuto)
        if self.mainBeams == BeamsEnum.DIPPED:
            headColor = self.COLOR_WHITE_DIPPED
            tailColor = self.COLOR_RED_TAIL
        elif self.mainBeams == BeamsEnum.HIGH:
            headColor = self.COLOR_WHITE_HIGH
            tailColor = self.COLOR_RED_TAIL
        else:
            headColor = self.COLOR_OFF
            tailColor = self.COLOR_OFF

        # 2. Brzdová světla (přepíší zadní obrysová na plnou červenou)
        if self.isBraking():
            tailColor = self.COLOR_RED_BRAKE

        self._setLedGroup(self.HEAD_LIGHTS, headColor)
        self._setLedGroup(self.BACK_LIGHTS, tailColor)

        # 3. Zpátečka (světlo na pozici 5 svítí bíle)
        if self.isReversing():
            self._setLedGroup(self.REVERSE_LIGHTS, self.COLOR_WHITE_REVERSE)

        # 4. Blinkry (přepíší diody 1,4 resp. 2,7 na oranžovou při pulzu)
        leftColor = self.COLOR_OFF
        rightColor = self.COLOR_OFF

        if self.indicator.indicatorLight is True:
            if self.indicator.isLeft():
                leftColor = self.COLOR_ORANGE
            if self.indicator.isRight():
                rightColor = self.COLOR_ORANGE

        self._setLedGroup(self.IND_LEFT, leftColor)
        self._setLedGroup(self.IND_RIGHT, rightColor)

        # Fyzický zápis do pásku (pokud auto_write=False)
        self._pixels.show()

    def render(self) -> None:
        """Okamžitě přepočte a zapíše barvy do LED bez čekání na periodu."""
        self._updateColors()

    def update(self, forwardSpeed: float = None, force: bool = False) -> None:
        """
        Periodická aktualizace celého světelného subsystému.
        Volá se v hlavní smyčce robota `robot.update()`.
        """
        if forwardSpeed is not None:
            self.setForwardSpeed(forwardSpeed)

        self.indicator.update()

        if force or self._showPeriod.isTime():
            self._updateColors()

    def off(self) -> None:
        """Nouzové zhasnutí všech světel."""
        self.mainBeams = BeamsEnum.OFF
        self.indicator.direction = None
        self.indicator.warning = False
        self._pixels.fill(self.COLOR_OFF)
        self._pixels.show()
