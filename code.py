from adafruit_ticks import ticks_ms, ticks_diff
from busio import I2C as BusIO_I2C
from picoed import i2c as pico_i2c, button_a, led, display
from neopixel import NeoPixel
from board import P0

class LogLevel:
    """Reprezentuje jednu úroveň logování.

    Atributy:
        name (str): Název úrovně (např. "INFO").
        value (int): Číselná priorita úrovně (vyšší = podrobnější log).
    """
    def __init__(self, name: str, value: int) -> None:
        self.name = name
        self.value = value


class LogLevelEnum:
    """Enum-like kolekce úrovní logování."""
    ERROR = LogLevel("ERROR", 1)
    WARNING = LogLevel("WARNING", 2)
    INFO = LogLevel("INFO", 3)
    DEBUG = LogLevel("DEBUG", 4)


class Log:
    """Jednoduchý logovací systém s časovými značkami.

    Atributy:
        level (LogLevel): Minimální úroveň logování.
        initTime (int): Čas inicializace loggeru v ms.
    """

    def __init__(self, level: LogLevel = LogLevelEnum.INFO) -> None:
        self._initTime: int = ticks_ms()
        self._level: LogLevel = level
        self._entries = []

    def _log(self, level: LogLevel, text: str) -> None:
        """Interní metoda pro výpis logu.

        Args:
            level (LogLevel): Úroveň zprávy.
            text (str): Text zprávy.
        """
        if self._level.value >= level.value:
            difTime_ms = ticks_ms() - self._initTime
            self._entries.append((difTime_ms, level.name, text))

    def flush(self, max_line: int = None) -> None:
        """Vytiskne všechny logy postupně a maže je."""
        count = 0
        while self._entries:
            difTime_ms, level_name, text = self._entries.pop(0)
            print(f"[{difTime_ms:6d} ms|{level_name:7}] {text}")
            count += 1
            if max_line is not None and count >= max_line:
                break

    def debug(self, text: str) -> None:
        """Zapíše ladicí zprávu."""
        self._log(LogLevelEnum.DEBUG, text)

    def info(self, text: str) -> None:
        """Zapíše informativní zprávu."""
        self._log(LogLevelEnum.INFO, text)

    def warning(self, text: str) -> None:
        """Zapíše varování."""
        self._log(LogLevelEnum.WARNING, text)

    def error(self, text: str) -> None:
        """Zapíše chybovou zprávu."""
        self._log(LogLevelEnum.ERROR, text)
    
    def exception(self, e: BaseException) -> None:
        """Zapíše výjimku jako chybu."""
        self.error(f"Exception: {str(e)}")


log = Log(level=LogLevelEnum.DEBUG)



class DirectionEnum:
    LEFT = "left"
    RIGHT = "right"
    FORWARD = "forward"
    BACKWARD = "backward"

class Timer:
    """Jednoduchý jednorázový časovač.

    Slouží pro měření uplynulého času a detekci timeoutu.

    Atributy:
        timeout_ms (int): Nastavený timeout v milisekundách.
        _startTime (int|None): Čas spuštění časovače.
    """

    def __init__(self, timeout_ms: int = None, startTimer: bool = True) -> None:
        self.timeout_ms = timeout_ms
        if startTimer:
            self.startTimer()
        else:
            self.stopTimer()

    def startTimer(self, start_time_ms: int = None, timeout_ms: int = None) -> None:
        """Spustí časovač.

        Args:
            start_time_ms (int): Počáteční čas (default: aktuální čas).
            timeout_ms (int): Nový timeout (volitelné).
        """
        if timeout_ms is not None:
            self.timeout_ms = timeout_ms
        self._startTime = self._getTime(start_time_ms)

    def stopTimer(self) -> None:
        """Zastaví časovač."""
        self._startTime = None

    def isStarted(self) -> bool:
        """Vrací True, pokud je časovač aktivní."""
        return self._startTime is not None

    def _getTime(self, time_ms: int) -> int:
        """Vrátí zadaný čas nebo aktuální čas v ms."""
        if time_ms is None:
            time_ms = ticks_ms()
        return time_ms

    def _getTimeout(self, timeout_ms: int = None) -> int:
        """Vrátí timeout – buď zadaný, nebo výchozí nebo nulovy."""
        if timeout_ms is None:
            timeout_ms = self.timeout_ms
        if timeout_ms is None:
            timeout_ms = 0
        return timeout_ms

    def getTimeDiff(self, test_time_ms: int = None) -> int:
        """Vrátí rozdíl času od spuštění."""
        self.lastTimeDiff = ticks_diff(self._getTime(test_time_ms), self._startTime)
        return self.lastTimeDiff

    def isTimeout(self, test_time_ms: int = None, timeout_ms: int = None) -> bool:
        """Vrátí True, pokud vypršel timeout."""
        if not self.isStarted():
            return False
        return self.getTimeDiff(test_time_ms) >= self._getTimeout(timeout_ms)


class Period(Timer):
    """Periodický časovač.

    Po dosažení timeoutu se automaticky restartuje.
    """

    def isTime(self, test_time_ms: int = None, timeout_ms: int = None) -> bool:
        """Vrátí True, pokud nastal čas události, a restartuje časovač."""
        time_ms = self._getTime(test_time_ms)
        ret = self.isTimeout(time_ms, timeout_ms)
        if ret:
            self.startTimer(time_ms)
        return ret


class I2C:
    """Bezpečný wrapper pro I2C komunikaci, který se používá výhradně 
    přes `with i2c:` (tím proběhne automatické zamknutí a automatické odemknutí). 
    Veřejné metody nepoužívají vlastní lock.

    Atributy:
        busio_i2c (BusIO_I2C): Podkladový I2C objekt.
    """
    def __init__(self, i2c: BusIO_I2C) -> None:
        self.busio_i2c = i2c

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
        if self.busio_i2c.try_lock():
            return
        # čekej na lock s timeoutem
        start = ticks_ms()
        while not self.busio_i2c.try_lock():
            if ticks_diff(ticks_ms(), start) > 5:
                e = TimeoutError("I2C lock timeout")
                log.exception(e)
                # není možné získat lock
                raise e

    def _unlock(self) -> None:
        """Uvolní I2C lock."""
        self.busio_i2c.unlock()

    # ---------------------------------------------------------
    # Veřejné metody — bez locku
    # ---------------------------------------------------------
    def scan(self) -> list[int]:
        """Vrátí seznam dostupných I2C adres."""
        return self.busio_i2c.scan()

    def read(self, addr: int, n: int) -> bytearray:
        """Přečte n bajtů z adresy."""
        buffer = bytearray(n)
        self.busio_i2c.readfrom_into(addr, buffer, start=0, end=n)
        return buffer

    def write(self, addr: int, buf: bytearray) -> None:
        """Zapíše buffer na adresu."""
        self.busio_i2c.writeto(addr, buf)

    def write_readinto(self, addr: int, write_buf: bytearray, read_buf: bytearray) -> None:
        """Zapíše a následně přečte data z adresy."""
        self.busio_i2c.writeto_then_readfrom(addr, write_buf, read_buf)


class PCF8574:
    """Ovladač PCF8574 I/O expanderu."""
    def __init__(self, i2c: I2C, address: int = 0x38) -> None:
        self._i2c = i2c
        self._address = address

    def write(self, data: int) -> None:
        """Zapíše data do expanderu."""
        with self._i2c:
            # automaticky provede lock
            self._i2c.write(self._address, bytes([data & 0xFF]))
            # automaticky provede unlock

    def read(self) -> int:
        """Přečte data z expanderu."""
        with self._i2c:
            # automaticky provede lock
            return self._i2c.read(self._address, 1)[0]
            # automaticky provede unlock


class PCA9633_registers:
    """Adresy registrů pro PWM driver PCA9633."""
    MODE1 = 0x00
    MODE2 = 0x01
    PWM0 = 0x02
    PWM1 = 0x03
    PWM2 = 0x04
    PWM3 = 0x05
    GRPPWM = 0x06
    GRPFREQ = 0x07
    LEDOUT = 0x08
    SUBADR1 = 0x09
    SUBADR2 = 0x0A
    SUBADR3 = 0x0B
    ALLCALLADR = 0x0C

class PCA9633:
    """Ovladač PWM driveru PCA9633.

    Umožňuje zápis a čtení registrů a řízení 4 PWM kanálů.
    """
    def __init__(self, i2c: I2C, address=0x62):
        self._i2c = i2c
        self._address = address

    def readRegister(self, reg: int) -> int:
        """Přečte hodnotu z registru."""
        readbuffer = bytearray(1)
        with self._i2c:
            # automaticky provede lock
            self._i2c.write_readinto(self._address, bytes([reg]), readbuffer)
            # automaticky provede unlock
        return readbuffer[0]

    def writeRegister(self, reg: int, value: int) -> None:
        """Zapíše hodnotu do registru."""
        with self._i2c:
            # automaticky provede lock
            self._i2c.write(self._address, bytes([reg, value]))
            # automaticky provede unlock

    def writeTwoRegisters(self, firstReg: int, firstValue: int, secondReg: int, secondValue: int) -> None:
        """Zapíše hodnoty do dvou registrů."""
        with self._i2c:
            # automaticky provede lock
            self._i2c.write(self._address, bytes([firstReg, firstValue]))
            self._i2c.write(self._address, bytes([secondReg, secondValue]))
            # automaticky provede unlock


i2c = I2C(pico_i2c)


class Sensors:
    """Reprezentuje sadu senzorů robota připojených přes PCF8574 I/O expander."""
    ObstacleRight = 0x40  # bit 6 - pravý senzor překážek
    ObstacleLeft = 0x20   # bit 5 - levý senzor překážek 

    LineRight = 0x10     # bit 4 - pravý senzor čáry 
    LineMiddle = 0x08    # bit 3 - střední senzor čáry
    LineLeft = 0x04      # bit 2 - levý senzor čáry
    LineAll = 0x1C       # všechny senzory čáry (pro otočení polarity)

    def __init__(self, pcf8574: PCF8574) -> None:
        """Inicializace vyčítání senzorů."""
        self._pcf8574 = pcf8574
        self._periodRead = Period(timeout_ms=50)
        self._data = -1
        self.updateSensorData()

    def updateSensorData(self) -> None:
        """Přečti data ze senzorů."""
        self._dataPrev = self._data
        self._data = self._pcf8574.read() ^ Sensors.LineAll
        if self._data != self._dataPrev:
            self.show(255,1)

    def show(self, bh: int = 9, bl: int = 1) -> None:
        """Zobrazí stav senzorů na vestavěném displeji."""
        display.pixel(16, 6, bh if self.areActive(Sensors.ObstacleLeft ) else bl)
        display.pixel(11, 6, bh if self.areActive(Sensors.LineLeft     ) else bl)
        display.pixel( 8, 6, bh if self.areActive(Sensors.LineMiddle   ) else bl)
        display.pixel( 5, 6, bh if self.areActive(Sensors.LineRight    ) else bl)
        display.pixel( 0, 6, bh if self.areActive(Sensors.ObstacleRight) else bl)
    def getSensorData(self, mask:int) -> int:
        return self._data & mask

    def areActive(self, sensor:int) -> bool:
        """Vrátí True pokud je senzor (všechny požadované) aktivní."""
        return self.getSensorData(sensor) == 0

    def isAnyActive(self, sensor:int) -> bool:
        """Vrátí True pokud je alespoň jeden ze senzorů aktivní?"""
        return self.getSensorData(sensor) != sensor

    def update(self) -> None:
        """Periodická aktualizace senzorů."""
        if self._periodRead.isTime():
            self.updateSensorData()

# maximální povolená hodnota PWM pro motory 
LIMIT_PWM = 255     # u PCA9633 je max 255, pro PCA9685 je to 4095


class Wheel:
    """Reprezentuje jeden motor robota.

    Zajišťuje:
        - řízení PWM,
        - bezpečnou změnu směru,
        - ochranné zpoždění při reverzu.
    """

    def __init__(self, side: DirectionEnum, pca9633: PCA9633) -> None:
        """Inicializuje motor podle jeho umístění (LEFT/RIGHT)."""
        self._side = side
        self._pca9633 = pca9633
        self._timer = Timer(startTimer=False)
        self._targetPwm = 0
        self._lastAppliedPwm = 0

        if side == DirectionEnum.RIGHT:
            self._regPwmBack = PCA9633_registers.PWM0
            self._regPwmForw = PCA9633_registers.PWM1
        elif side == DirectionEnum.LEFT:
            self._regPwmBack = PCA9633_registers.PWM2
            self._regPwmForw = PCA9633_registers.PWM3
        else:
            e = ValueError("Wheel: Invalid side")
            log.exception(e)
            raise e

    def _applyDeadzone(self, pwm:int) -> int:
        """Omezí PWM na minimální absolutní hodnotu (pri mensi se nerozjede motor)."""
        dead = 20 # self.calibrateFactors.getMinimumPwm(self.isStopped())
        if abs(pwm) < dead:
            pwm = dead if pwm > 0 else -dead
            log.debug(f"minimumPwm {pwm}")
        return pwm

    def _enforceMaximumPwm(self, pwm: int) -> int:
        """Omezí PWM na maximální absolutní hodnotu kterou dovoluje HW."""
        if abs(pwm) > LIMIT_PWM:
            pwm = LIMIT_PWM if pwm > 0 else -LIMIT_PWM
            log.debug(f"maximumPwm {pwm}")
        return pwm

    def stop(self) -> None:
        """Zastaví motor."""
        self.ridePwm(0)

    def _sanitizePwm(self, pwm: int) -> int:
        if pwm == 0:
            return 0
        pwm = self._applyDeadzone(pwm)
        pwm = self._enforceMaximumPwm(pwm)
        return pwm

    def ridePwm(self, pwm: int) -> None:
        """Nastaví PWM motoru (s omezením).
        Args:
            pwm (int): Požadovaná PWM hodnota.
        """
        pwm = self._sanitizePwm(pwm)
        self._targetPwm = pwm
        self._applyPwmSafely()

    def _hasDirectionChanged(self) -> bool:
        """Vrací True, pokud dochází ke změně směru."""
        return (self._lastAppliedPwm * self._targetPwm) < 0
#        return (self._lastAppliedPwm > 0 and self._targetPwm < 0) or \
#               (self._lastAppliedPwm < 0 and self._targetPwm > 0)

    def _applyPwmRaw(self, pwm: int) -> None:
        """Zapíše PWM přímo do driveru."""
        if pwm >= 0:
            self._pca9633.writeTwoRegisters(self._regPwmBack, 0, self._regPwmForw, pwm)
        else:
            self._pca9633.writeTwoRegisters(self._regPwmForw, 0, self._regPwmBack, -pwm)
        self._lastAppliedPwm = pwm
        log.debug(f"Wheel {self._side} - PWM set to {pwm}")
                  

    def _applyPwmSafely(self) -> None:
        """Bezpečně aplikuje PWM na motor (řeší zpoždění při reverzu)."""
        if self._targetPwm == self._lastAppliedPwm:
            # pwm se nezměnilo (není důvod ho znovu poslat)
            return

        if self._hasDirectionChanged():
            # detekována změna směru – nejdříve zastav motor a chvíli počkej (100 ms)
            log.debug("Wheel direction change detected, stopping motor for safety.")
            self._applyPwmRaw(0)
            self._timer.startTimer(timeout_ms=100)

        if self._timer.isStarted():
            # čekej na uplynutí zpoždění
            if not self._timer.isTimeout():
                # ještě neuplynul čas zpoždění
                return
            self._timer.stopTimer()

        # nyní může být PWM bezpečně zasláno do driveru
        self._applyPwmRaw(self._targetPwm)

    def update(self) -> None:
        """Periodická aktualizace motoru."""
        self._applyPwmSafely()

class Wheels:
    """Řídí dvojici motorů (levý + pravý) jako diferenciální podvozek."""
    def __init__(self, pca9633: PCA9633) -> None:
        self._pca9633 = pca9633
        self._wheels = {
            DirectionEnum.LEFT:  Wheel(DirectionEnum.LEFT,  pca9633),
            DirectionEnum.RIGHT: Wheel(DirectionEnum.RIGHT, pca9633),
        }
        self._initMotorDriver()

    @property
    def left(self) -> Wheel:
        return self._wheels[DirectionEnum.LEFT]

    @property
    def right(self) -> Wheel:
        return self._wheels[DirectionEnum.RIGHT]


    def _initMotorDriver(self) -> None:
        """Inicializuje PCA9633 driver pro řízení motorů."""
        self._pca9633.writeTwoRegisters(PCA9633_registers.MODE1, 0x00, PCA9633_registers.LEDOUT, 0xAA)

    def emergencyShutdown(self) -> None:
        """Bezpečně zastaví všechny motory a ohlásí chyby."""
        log.info("Emergency stop!")
        exceptions = []
        for wheel in self._wheels.values():
            try:
                wheel.stop()
            except BaseException as e:
                exceptions.append(e)
        if exceptions:
            e = RuntimeError("Chyba při odstavení motorů", exceptions)
            log.exception(e)
            raise e

    def ridePwm(self, pwms: list[int]) -> None:
        """Nastaví PWM pro oba motory."""
        for wheel, pwm in zip(self._wheels.values(), pwms):
            wheel.ridePwm(pwm)

    def stop(self) -> None:
        """Zastaví oba motory."""
        for wheel in self._wheels.values():
            wheel.stop()

    def update(self) -> None:
        """Periodicky aktualizuje oba motory."""
        for wheel in self._wheels.values():
            wheel.update()


class Robot:
    """Hlavní třída robota."""
    def __init__(self, i2c: I2C) -> None:
        pcf8574 = PCF8574(i2c)
        pca9633 = PCA9633(i2c)
        self.sensors = Sensors(pcf8574)
        self.wheels = Wheels(pca9633)

    def update(self) -> None:
        """Periodická aktualizace robota."""
        self.sensors.update()
        self.wheels.update()

    def stop(self) -> None:
        """Zastaví robota."""
        self.wheels.stop()

    def emergencyShutdown(self) -> None:
        """Bezpečně zastaví robota."""
        self.wheels.emergencyShutdown()

def createJoyCarRobot() -> Robot:
    """Vytvoří a vrátí instanci robota."""
    return Robot(i2c)

if __name__ == "__main__":

    try:
        log.info("Program started.")

        nextSpeed = Period(timeout_ms=3000)
        speeds = [
            [ 150,  150],
            [-150,  100],
            [-100, -150],
            [ 100,  100],
        ]
        light = NeoPixel(P0, 8)
        joyCar = None
        x = 0
        try:            
            joyCar = createJoyCarRobot()
            
            while not button_a.is_pressed():
                if nextSpeed.isTime():
                    log.flush(max_line=50)
                    led.toggle()
                    x += 20
                    light.fill((x, 0, 0))
                    if speeds == []:
                        log.info("Last speed reached.")
                        break
                    log.info("Next speed.")
                    joyCar.wheels.ridePwm(speeds.pop(0))
                joyCar.update()

            log.info("Stopping robot...")
            joyCar.wheels.stop()
        
        except Exception as e:
            log.exception(e)
            if joyCar is not None:
                joyCar.emergencyShutdown()
            raise e

        log.info("Program ended.")
        log.flush()
                
        print("Press button A to exit...")
        while not button_a.is_pressed():
            joyCar.update()
            
    finally:        
        led.off()
        light.fill((0, 0, 0))
        display.clear()
        