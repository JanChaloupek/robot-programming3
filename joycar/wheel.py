"""
wheel.py – Řízení jednoho motoru robota JoyCar.

Tento modul poskytuje třídu Wheel, která:
- řídí jeden motor pomocí I2C driveru (PCA9633 pro 0–255 nebo PCA9685 pro 0–4095),
- podporuje volitelnou kalibraci CalibrateFactors (vychází z 1-SW_GIT a 2-SW_GIT),
- aplikuje deadzone (minimální rozjezdové PWM) a omezuje maximální povolené PWM,
- řeší bezpečné reverzní zpoždění (přechod přes nulu) při změně směru otáčení,
- umožňuje řízení pomocí PWM, otáček za sekundu (RPS) i lineární rychlosti v m/s.
"""

from typing import Optional, Any
from joycar.constants import PI
from joycar.direction import DirectionEnum
from joycar.pca9633 import PCA9633_registers
from joycar.calibration import CalibrateFactors
from utils import Timer, log

LIMIT_PWM = 255  # Výchozí limit pro standardní 8bitový čip PCA9633


class Wheel:
    """Reprezentuje jeden motor kola robota JoyCar."""

    # Výchozí převod RPS → PWM pro nezkalibrovaný 8bitový motor
    _DEFAULT_PWM_PER_RPS = 200

    def __init__(self,
                 side: DirectionEnum,
                 driver: Any,
                 diameter: float = 0.065,
                 calibration: Optional[CalibrateFactors] = None,
                 maxPwm: Optional[int] = None) -> None:
        """
        Inicializuje motor podle jeho strany, driveru a parametrů kola.

        Args:
            side (DirectionEnum): Strana motoru (LEFT nebo RIGHT).
            driver (Any): Budič motoru (PCA9633 nebo PCA9685).
            diameter (float): Průměr kola v metrech (výchozí 0.065 m).
            calibration (Optional[CalibrateFactors]): Kalibrační koeficienty motoru.
            maxPwm (Optional[int]): Maximální rozsah PWM (255 nebo 4095).
                Při nezadání se určí automaticky z driveru / kalibrace.
        """
        self._side = side
        self._driver = driver
        self._pca9633 = driver  # Zachování zpětné kompatibility atributu
        self._calibration = calibration
        self._timer = Timer(startTimer=False)
        self._targetPwm = 0
        self._lastAppliedPwm = 0

        # Uložení rozměrů kola
        self._diameter = diameter
        self._circumference = PI * diameter

        # Zjištění maximálního rozsahu PWM (255 vs 4095)
        if maxPwm is not None:
            self._maxPwm = maxPwm
        elif calibration is not None:
            self._maxPwm = calibration.maxPwm
        elif hasattr(driver, "MAX_PWM"):
            self._maxPwm = driver.MAX_PWM
        else:
            self._maxPwm = LIMIT_PWM

        # Nastavení minimálního PWM pro rozjezd (deadzone)
        if calibration is not None:
            self._deadzone = calibration.minPwm_WhenStopped
        elif self._maxPwm > 255:
            # Proporcionální deadzone pro 12bitový HW (cca 320 z 4095 odpovídá 20 z 255)
            self._deadzone = int(self._maxPwm * (20.0 / 255.0))
        else:
            self._deadzone = 20

        # Mapování kanálů a registrů podle strany a typu budiče
        if side == DirectionEnum.RIGHT:
            self._channel = 0  # PCA9685 kanál 0 a 1
            self._regPwmBack = PCA9633_registers.PWM0
            self._regPwmForw = PCA9633_registers.PWM1
        elif side == DirectionEnum.LEFT:
            self._channel = 2  # PCA9685 kanál 2 a 3
            self._regPwmBack = PCA9633_registers.PWM2
            self._regPwmForw = PCA9633_registers.PWM3
        else:
            raise ValueError("Wheel: Neplatná strana motoru.")

    @property
    def maxPwm(self) -> int:
        """Maximální povolená hodnota PWM pro tento motor."""
        return self._maxPwm

    @property
    def calibration(self) -> Optional[CalibrateFactors]:
        return self._calibration

    @calibration.setter
    def calibration(self, cal: CalibrateFactors) -> None:
        self._calibration = cal
        self._maxPwm = cal.maxPwm
        self._deadzone = cal.minPwm_WhenStopped

    # ---------------------------------------------------------
    # Veřejné metody – řízení rychlosti
    # ---------------------------------------------------------

    def setSpeed(self, pwm: int) -> None:
        """
        Nastaví rychlost kola přímo pomocí PWM.

        Kladné hodnoty = dopředu.
        Záporné hodnoty = dozadu.
        0 = stop.
        """
        pwm = self._sanitizePwm(pwm)
        self._targetPwm = pwm
        self._applyPwmSafely()

    def stop(self) -> None:
        """Bezpečně zastaví motor (nastaví PWM na 0)."""
        self.setSpeed(0)

    def setAngularSpeed(self, rps: float) -> None:
        """
        Nastaví rychlost kola v otáčkách za sekundu (RPS).
        Při zadané kalibraci využije naměřený lineární přepočet PWM = a * omega + b.
        """
        if self._calibration is not None:
            omega = rps * 2 * PI  # Převod na úhlovou rychlost v rad/s
            pwm = self._calibration.calculatePwm(omega)
        else:
            scale = self._maxPwm / 255.0
            pwm = int(rps * self._DEFAULT_PWM_PER_RPS * scale)
        self.setSpeed(pwm)

    def setAngularSpeedRad(self, omegaRad: float) -> None:
        """Nastaví rychlost kola přímo v radiánech za sekundu (rad/s)."""
        rps = omegaRad / (2 * PI)
        self.setAngularSpeed(rps)

    def setLinearSpeed(self, vMps: float) -> None:
        """
        Nastaví dopřednou rychlost kola v metrech za sekundu (m/s).
        m/s → RPS → PWM
        """
        rps = vMps / self._circumference
        self.setAngularSpeed(rps)

    # ---------------------------------------------------------
    # Interní pomocné metody
    # ---------------------------------------------------------

    def _applyDeadzone(self, pwm: int) -> int:
        """Aplikuje minimální PWM pro spolehlivý rozjezd z klidu."""
        dead = self._deadzone
        if abs(pwm) < dead:
            pwm = dead if pwm > 0 else -dead
        return pwm

    def _enforceMaximumPwm(self, pwm: int) -> int:
        """Omezí PWM na maximum podle osazeného hardware (255 nebo 4095)."""
        limit = self._maxPwm
        if abs(pwm) > limit:
            pwm = limit if pwm > 0 else -limit
        return pwm

    def _sanitizePwm(self, pwm: int) -> int:
        """Normalizuje PWM: nula zůstává nula, malé hodnoty se zvýší na deadzone a omezí se na max."""
        if pwm == 0:
            return 0
        pwm = self._applyDeadzone(pwm)
        pwm = self._enforceMaximumPwm(pwm)
        return pwm

    def _hasDirectionChanged(self) -> bool:
        """Vrací True, pokud se mění směr otáčení motoru."""
        return (self._lastAppliedPwm * self._targetPwm) < 0

    def _applyPwmRaw(self, pwm: int) -> None:
        """Zapíše PWM přímo do hardware podle typu použitého budiče."""
        # 1. Varianta PCA9685 (metoda writePwmToHbridge pro rozsah -4095 .. +4095)
        if hasattr(self._driver, "writePwmToHbridge"):
            self._driver.writePwmToHbridge(self._channel, pwm)
        # 2. Varianta PCA9633 (metoda writeTwoRegisters pro rozsah -255 .. +255)
        elif hasattr(self._driver, "writeTwoRegisters"):
            if pwm >= 0:
                self._driver.writeTwoRegisters(self._regPwmBack, 0,
                                               self._regPwmForw, pwm)
            else:
                self._driver.writeTwoRegisters(self._regPwmForw, 0,
                                               self._regPwmBack, -pwm)
        self._lastAppliedPwm = pwm

    def _applyPwmSafely(self) -> None:
        """
        Bezpečně aplikuje PWM na motor s ochranou H-můstku:
        Při změně směru nejprve motory odpojí (PWM=0), vyčká 100 ms na doběhnutí rotoru
        a teprve poté sepne opačný směr.
        """
        if self._targetPwm == self._lastAppliedPwm:
            return

        if self._hasDirectionChanged():
            self._applyPwmRaw(0)
            log.debug(f"Wheel {self._side}: reverzní zpoždění aktivováno.")
            self._timer.startTimer(timeout_ms=100)

        if self._timer.isStarted() and not self._timer.isTimeout():
            return

        self._timer.stopTimer()
        self._applyPwmRaw(self._targetPwm)

    def update(self) -> None:
        """Periodická aktualizace motoru v hlavní smyčce."""
        self._applyPwmSafely()
