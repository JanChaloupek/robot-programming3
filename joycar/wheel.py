"""
wheel.py – řízení jednoho motoru robota JoyCar.

Tento modul poskytuje třídu Wheel, která:
- řídí jeden motor pomocí PCA9633,
- aplikuje deadzone (minimální PWM pro rozjezd),
- řeší bezpečné reverzní zpoždění při změně směru,
- umožňuje řízení pomocí PWM, rychlosti v m/s i otáček za sekundu.

Použití:
    wheel = Wheel(DirectionEnum.LEFT, pca9633, diameter=0.065)
    wheel.setLinearSpeed(0.2)
"""

from joycar.constants import PI
from joycar.pca9633 import PCA9633, PCA9633_registers
from joycar.direction import DirectionEnum
from utils import Timer, log

LIMIT_PWM = 255


class Wheel:
    """Reprezentuje jeden motor robota JoyCar."""

    # kalibrační konstanta: převod RPS → PWM
    # (uživatel si ji může později nakalibrovat)
    _PWM_PER_RPS = 200

    def __init__(self, side: DirectionEnum, pca9633: PCA9633, diameter: float) -> None:
        """
        Inicializuje motor podle jeho strany (levý/pravý) a průměru kola.

        Args:
            side (DirectionEnum): strana motoru
            pca9633 (PCA9633): driver motoru
            diameter (float): průměr kola v metrech
        """
        self._side = side
        self._pca9633 = pca9633
        self._timer = Timer(startTimer=False)
        self._targetPwm = 0
        self._lastAppliedPwm = 0

        # uložení průměru a výpočet obvodu kola
        self._diameter = diameter
        self._circumference = PI * diameter

        # mapování PWM registrů podle strany
        if side == DirectionEnum.RIGHT:
            self._regPwmBack = PCA9633_registers.PWM0
            self._regPwmForw = PCA9633_registers.PWM1
        elif side == DirectionEnum.LEFT:
            self._regPwmBack = PCA9633_registers.PWM2
            self._regPwmForw = PCA9633_registers.PWM3
        else:
            raise ValueError("Wheel: Neplatná strana motoru.")

    # ---------------------------------------------------------
    # Veřejné metody – řízení rychlosti
    # ---------------------------------------------------------

    def setSpeed(self, pwm: int) -> None:
        """
        Nastaví rychlost kola pomocí PWM.

        Kladné hodnoty = dopředu  
        Záporné hodnoty = dozadu
        """
        pwm = self._sanitizePwm(pwm)
        self._targetPwm = pwm
        self._applyPwmSafely()

    def stop(self) -> None:
        """Zastaví motor (nastaví PWM na 0)."""
        self.setSpeed(0)

    def setAngularSpeed(self, rps: float) -> None:
        """
        Nastaví rychlost kola v otáčkách za sekundu (RPS).

        RPS → PWM (pomocí kalibrace)
        """
        pwm = int(rps * self._PWM_PER_RPS)
        self.setSpeed(pwm)

    def setLinearSpeed(self, vMps: float) -> None:
        """
        Nastaví rychlost kola v metrech za sekundu.

        m/s → RPS → PWM
        """
        rps = vMps / self._circumference
        self.setAngularSpeed(rps)

    # ---------------------------------------------------------
    # Interní pomocné metody
    # ---------------------------------------------------------

    def _applyDeadzone(self, pwm: int) -> int:
        """Aplikuje minimální PWM, aby se motor skutečně rozjel."""
        dead = 20
        if abs(pwm) < dead:
            pwm = dead if pwm > 0 else -dead
        return pwm

    def _enforceMaximumPwm(self, pwm: int) -> int:
        """Omezí PWM na maximální hodnotu povolenou hardwarem."""
        if abs(pwm) > LIMIT_PWM:
            pwm = LIMIT_PWM if pwm > 0 else -LIMIT_PWM
        return pwm

    def _sanitizePwm(self, pwm: int) -> int:
        """Aplikuje deadzone a omezení maximální hodnoty."""
        if pwm == 0:
            return 0
        pwm = self._applyDeadzone(pwm)
        pwm = self._enforceMaximumPwm(pwm)
        return pwm

    def _hasDirectionChanged(self) -> bool:
        """Vrací True, pokud došlo ke změně směru otáčení."""
        return (self._lastAppliedPwm * self._targetPwm) < 0

    def _applyPwmRaw(self, pwm: int) -> None:
        """Zapíše PWM přímo do driveru PCA9633."""
        if pwm >= 0:
            self._pca9633.writeTwoRegisters(self._regPwmBack, 0,
                                            self._regPwmForw, pwm)
        else:
            self._pca9633.writeTwoRegisters(self._regPwmForw, 0,
                                            self._regPwmBack, -pwm)
        self._lastAppliedPwm = pwm

    def _applyPwmSafely(self) -> None:
        """
        Bezpečně aplikuje PWM na motor.

        Pokud dojde ke změně směru:
            - motor se nejprve zastaví,
            - počká se 100 ms,
            - teprve poté se aplikuje nový PWM.
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
        """Periodická aktualizace motoru."""
        self._applyPwmSafely()
