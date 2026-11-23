"""
robot.py – Hlavní řídicí třída (fasáda) robota JoyCar s Pico:ed.

Vzorový výukový modul pro studenty:
-----------------------------------
Tento modul představuje ústředního „dirigenta“ celého robota podle vzoru Superloop
(viz metafora orchestru v studijním materiálu:
 https://github.com/JanChaloupek/pomucky/blob/main/superloop.md).

Architektura robota:
--------------------
Třída JoyCarRobot sdružuje všechny hardwarové subsystémy do jednotného a snadno
použitelného rozhraní (Design Pattern: Facade):
1. `self.sensors` : Čtení infračervených senzorů čáry a překážek (přes I2C expandér PCF8574).
2. `self.wheels`  : Diferenciální podvozek – dva stejnosměrné motory řízené PWM řadičem PCA9633.
3. `self.lights`  : NeoPixel světelný subsystém (potkávací/dálková světla, blinkry, brzdová světla).
4. `display`      : Čelní LED maticový displej Pico:ed (17x7 bodů) s rychlým framebufferem.

Neblokující řízení:
-------------------
Robot v metodě `update()` jednou za cyklus superloopu předá řízení všem subsystémům.
Žádná operace neblokuje běh procesoru voláním sleep().

Příklad základního použití studentem:
-------------------------------------
    from picoed import i2c as pico_i2c
    from joycar import JoyCarRobot, I2C

    # 1. Inicializace robota
    robot = JoyCarRobot(I2C(pico_i2c))

    # 2. Superloop smyčka
    while True:
        robot.rideLine(baseSpeed=0.2)
        robot.update()
"""

import board
from utils.timer import Timer
from utils.log import log
from joycar.display import display
from joycar.i2c import I2C
from joycar.pcf8574 import PCF8574
from joycar.pca9633 import PCA9633
from joycar.sensors import Sensors, LineSituationEnum, CrossRoadType
from joycar.wheels import Wheels
from joycar.lights import LightsControl, BeamsEnum
from joycar.direction import DirectionEnum
from joycar.sound import HornController, HonkData
from joycar.calibration import CalibrateFactors
from joycar.pca9685 import PCA9685
from joycar.lcd import TextDisplay


class JoyCarRobot:
    """
    Hlavní třída reprezentující sestaveného robota JoyCar.

    Poskytuje vysokoúrovňové metody pro sledování čáry, řízení rychlosti,
    ovládání světel a periodickou aktualizaci stavu.
    """

    def __init__(
        self,
        i2c: I2C,
        wheelDiameter: float = 0.065,
        wheelBase: float = 0.095,
        neopixel_pin = board.P0,
        lights: LightsControl = None,
        buzzer_pin = None,
        horn: HornController = None,
        line_sensors: int = 3,
        driver: Any = None,
        calibration: CalibrateFactors = None,
        lcd: TextDisplay = None,
        lcd_enabled: bool = False
    ) -> None:
        """
        Inicializuje všechny periferie a subsystémy robota JoyCar.

        Args:
            i2c (I2C): Zabezpečený I2C wrapper s context-managerem pro automatické zamykání sběrnice.
            wheelDiameter (float): Průměr hnacích kol v metrech (výchozí 0.065 m = 65 mm).
            wheelBase (float): Vzdálenost mezi středy kol v metrech (výchozí 0.095 m = 95 mm).
            neopixel_pin: Pin mikrokontroléru připojený k LED pásku (výchozí P0).
            lights (LightsControl|None): Volitelná instance světelného subsystému (pro testy s test-double).
            buzzer_pin: Pin mikrokontroléru připojený k bzučáku (výchozí board.BUZZER).
            horn (HornController|None): Volitelná instance zvukového kontroléru.
            line_sensors (int): Počet senzorů čáry (2, 3, 4, 5 nebo 6). Výchozí: 3.
            driver (Any|None): Budič motorů (PCA9633, PCA9685 nebo řetězec 'PCA9685').
            calibration (CalibrateFactors|None): Volitelná kalibrace motorů.
            lcd (TextDisplay|None): Volitelná instance textového LCD displeje.
            lcd_enabled (bool): Zda má být textový LCD displej aktivní (výchozí False).
        """
        self._i2c = i2c

        # Inicializace I2C čipů podvozku
        pcf8574 = PCF8574(i2c)

        # Volba budiče motorů podle zadaného HW (PCA9633 vs PCA9685)
        if driver == "PCA9685":
            motor_driver = PCA9685(i2c)
        elif driver is not None:
            motor_driver = driver
        else:
            motor_driver = PCA9633(i2c)

        # Inicializace subsystémů robota
        self.sensors = Sensors(pcf8574, lineSensorCount=line_sensors)
        self.wheels = Wheels(motor_driver, diameter=wheelDiameter, wheelBase=wheelBase, calibration=calibration)

        if lights is not None:
            self.lights = lights
        else:
            self.lights = LightsControl(pin=neopixel_pin, num_pixels=8)

        if buzzer_pin is None and hasattr(board, "BUZZER"):
            buzzer_pin = board.BUZZER

        if horn is not None:
            self.horn = horn
        else:
            self.horn = HornController(pin=buzzer_pin)

        # Textový LCD displej (volitelný, lze zapnout/vypnout)
        if lcd is not None:
            self.lcd = lcd
        else:
            self.lcd = TextDisplay(i2c, enabled=lcd_enabled)

        # Aktuální kinematický stav robota
        self._linearSpeed = 0.0
        self._angularSpeed = 0.0

        # Časovače pro křižovatkové manévry
        self._exitCrossRoadsTimer = Timer(timeout_ms=300, startTimer=False)
        self._turnErrorTimer = Timer(timeout_ms=400, startTimer=False)

        log.info("JoyCarRobot inicializovan")

    # -------------------------------------------------------------------------
    # Klíčová metoda superloopu
    # -------------------------------------------------------------------------

    def update(self) -> None:
        """
        Periodická aktualizace všech subsystémů robota.

        Tato metoda se musí volat v každém průchodu hlavní smyčky `while True:`
        (viz doporučení v superloop.md). Zajistí:
        1. Načtení dat ze senzorů (čára + překážky) a přepočet logiky.
        2. Bezpečný zápis PWM na motory (ošetření reverzní ochrany a deadzone).
        3. Aktualizaci blinkrů, brzdových a obrysových světel podle rychlosti.
        4. Krokování neblokujícího přehrávání tónů bzučáku.
        5. Odeslání změn framebufferu na displej Pico:ed.
        """
        self.sensors.update()
        self.wheels.update()
        self.lights.update(forwardSpeed=self._linearSpeed)
        self.horn.update()
        display.updatePixels()

    # -------------------------------------------------------------------------
    # Pohyb a kinematika podvozku
    # -------------------------------------------------------------------------

    def setVelocity(self, vMps: float, omegaRad: float = 0.0) -> None:
        """
        Nastaví požadovanou dopřednou a úhlovou rychlost robota.

        Vysvětlení diferenciální kinematiky pro studenty:
        - vMps (float): Dopředná rychlost v metrech za sekundu (m/s).
            Kladná = jízda vpřed, záporná = couvání, 0 = stojíme nebo rotujeme na místě.
        - omegaRad (float): Úhlová rychlost zatáčení v radiánech za sekundu (rad/s).
            Kladná hodnota = zatáčení doleva (levé kolo zpomalí, pravé zrychlí).
            Záporná hodnota = zatáčení doprava (pravé kolo zpomalí, levé zrychlí).
            0.0 = přímá jízda bez zatáčení.
        """
        self._linearSpeed = vMps
        self._angularSpeed = omegaRad
        self.lights.setForwardSpeed(vMps)
        self.wheels.setVelocity(vMps, omegaRad)
        log.debug(f"Velocity: v={vMps:.2f} m/s, w={omegaRad:.2f} rad/s")

    def rideLine(self, baseSpeed: float = 0.2, turnGain: float = 0.5) -> None:
        """
        Proporcionální autonomní sledování čáry pomocí čelních IR senzorů.

        Princip pro studenty:
        - Metoda `sensors.getLineDirection()` vrátí odchylku od -3 (prudce vpravo)
          do +3 (prudce vlevo).
        - Odchylku vynásobíme koeficientem zesílení `turnGain` (P-složka regulátoru),
          čímž získáme potřebnou úhlovou rychlost pro zatáčení.
        - Pokud je robot na středu (direction == 0), úhlová rychlost je nulová
          a robot jede plnou rychlostí `baseSpeed` rovně.

        Args:
            baseSpeed (float): Dopředná rychlost v m/s (výchozí 0.2 m/s).
            turnGain (float): Koeficient citlivosti zatáčení (čím vyšší, tím ostřeji točí).
        """
        direction = self.sensors.getLineDirection()

        # Pokud jsme mimo čáru nebo na křižovatce, neprovádíme korekci směru
        if direction is None:
            return

        # Výpočet úhlové rychlosti (kladný směr = vlevo, záporný = vpravo)
        omega = direction * turnGain
        self.setVelocity(baseSpeed, omega)

    def stop(self) -> None:
        """
        Bezpečně zastaví oba motory a aktivuje brzdová světla.
        """
        self.setVelocity(0.0, 0.0)
        self.wheels.stop()
        log.info("JoyCarRobot: stop")

    def emergencyShutdown(self) -> None:
        """
        Nouzové bezpečnostní zastavení všech subsystémů.
        Zastaví motory, okamžitě zhasne všechna světla a ztiší bzučák.
        """
        self._linearSpeed = 0.0
        self._angularSpeed = 0.0
        self.lights.off()
        self.horn.stop()
        self.wheels.emergencyShutdown()
        log.error("JoyCarRobot: emergencyShutdown!")

    def playHonk(self, honk_data: HonkData) -> None:
        """
        Spustí neblokující přehrávání znělky / melodie na bzučáku.

        Args:
            honk_data (HonkData): Definice sekvence tónů (např. tutu, brzdeni, hello).
        """
        log.info(f"JoyCarRobot: playHonk ({len(honk_data)} tonu)")
        self.horn.play(honk_data)

    def stopHonk(self) -> None:
        """Okamžitě ztiší bzučák."""
        self.horn.stop()

    # -------------------------------------------------------------------------
    # Pomocné metody pro navigaci
    # -------------------------------------------------------------------------

    def exitCrossRoads_start(self, timeoutMs: int = 300) -> None:
        """Spustí časovač pro vyjetí středu otáčení nad křižovatku."""
        self._exitCrossRoadsTimer.startTimer(timeout_ms=timeoutMs)

    def exitCrossRoads(self, direction, forward: float = 0.15, angular: float = 0.0) -> bool:
        """
        Popojede křižovatkou daným směrem, aby byl střed otáčení přesně nad křižovatkou.

        Returns:
            bool: True, pokud uplynul potřebný čas na opuštění čáry, jinak False.
        """
        # Pokud máme zadaný směr zatáčení, mírně podpoříme natočení
        if direction in (DirectionEnum.LEFT, "left", 1):
            angular = 0.3
        elif direction in (DirectionEnum.RIGHT, "right", 2):
            angular = -0.3
        else:
            angular = 0.0

        self.setVelocity(forward, angular)
        return self._exitCrossRoadsTimer.isTimeout()

    def turningToLine_start(self, timeoutMs: int = 400) -> None:
        """
        Spustí časovač pro bezpečné otočení na novou čáru.
        Minimální čas (např. 400 ms) brání okamžitému 'chycení' původní příčné čáry.
        """
        self._turnErrorTimer.startTimer(timeout_ms=timeoutMs)

    def turningToLine(self, direction, angularSpeed: float = 1.2) -> bool:
        """
        Otáčí robot na místě daným směrem, dokud střední senzor nezachytí novou čáru.

        Returns:
            bool: True, jakmile je otočení na novou čáru úspěšně dokončeno.
        """
        if direction in (DirectionEnum.LEFT, "left", 1):
            omega = angularSpeed
            self.lights.indicator.direction = DirectionEnum.LEFT
        elif direction in (DirectionEnum.RIGHT, "right", 2):
            omega = -angularSpeed
            self.lights.indicator.direction = DirectionEnum.RIGHT
        else:
            omega = 0.0

        # Otáčení na místě (dopředná rychlost = 0)
        self.setVelocity(0.0, omega)

        # Čáru můžeme úspěšně detekovat až po uplynutí minimálního času otočení
        if self._turnErrorTimer.isTimeout():
            if self.sensors.areActive(Sensors.LineMiddle):
                # Čára úspěšně chycena -> vypneme blinkr a manévr končí
                self.lights.indicator.direction = None
                return True

        return False

    def getSituationLine(self) -> int | None:
        """
        Vrátí celkovou situaci na trati:
        - LineSituationEnum.CROSSROADS : Stojíme na křižovatce / kolmé čáře.
        - LineSituationEnum.LINE       : Jedeme po čáře (nebo v tolerančním oknu).
        - None                         : Definitivní ztráta čáry (robot sjel z trasy).
        """
        return self.sensors.getSituationLine()


def createTestWheels():
    """Pomocná funkce pro vytvoření testovací instance Wheels pro JoyCar."""
    from picoed import i2c as i2c_picoed
    WHEEL_DIAMETER = 0.065
    ROBOT_DIAMETER = 0.095

    i2c = I2C(i2c_picoed)
    return Wheels(
        pca9633=PCA9633(i2c),
        diameter=WHEEL_DIAMETER,
        wheelBase=ROBOT_DIAMETER
    )
