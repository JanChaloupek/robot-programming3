"""
wheels.py – Řízení obou motorů JoyCar robota.

Tento modul poskytuje třídu Wheels, která:
- obsahuje dvojici motorů (levý + pravý),
- inicializuje driver motorů (PCA9633 pro 0–255 nebo PCA9685 pro 0–4095),
- umožňuje současné řízení obou motorů,
- podporuje diferenciální kinematiku podvozku robota (dopředná rychlost v, úhlová rychlost omega).
"""

from typing import Optional, Any
from joycar.wheel import Wheel
from joycar.direction import DirectionEnum
from joycar.pca9633 import PCA9633_registers
from joycar.calibration import CalibrateFactors
from utils.log import log


class Wheels:
    """Řídí dvojici motorů (levý + pravý podvozek)."""

    def __init__(self,
                 driver: Any,
                 diameter: float = 0.065,
                 wheelBase: float = 0.14,
                 calibration: Optional[CalibrateFactors] = None) -> None:
        """
        Inicializuje dvojici kol a parametry podvozku.

        Args:
            driver (Any): Budič motorů (PCA9633 nebo PCA9685).
            diameter (float): Průměr kol v metrech (výchozí 0.065 m).
            wheelBase (float): Rozvor (vzdálenost mezi koly) v metrech (výchozí 0.14 m).
            calibration (Optional[CalibrateFactors]): Kalibrační hodnoty motorů.
        """
        self._driver = driver
        self._pca9633 = driver  # Zachování zpětné kompatibility atributu
        self._halfWheelBase = wheelBase / 2
        self._calibration = calibration

        self._wheels = {
            DirectionEnum.LEFT: Wheel(DirectionEnum.LEFT, driver, diameter, calibration=calibration),
            DirectionEnum.RIGHT: Wheel(DirectionEnum.RIGHT, driver, diameter, calibration=calibration),
        }

        self._initMotorDriver()

    @property
    def left(self) -> Wheel:
        """Přístup k levému motoru."""
        return self._wheels[DirectionEnum.LEFT]

    @property
    def right(self) -> Wheel:
        """Přístup k pravému motoru."""
        return self._wheels[DirectionEnum.RIGHT]

    @property
    def driver(self) -> Any:
        return self._driver

    def _initMotorDriver(self) -> None:
        """Inicializuje driver motorů (probuzení ze spánku a nastavení PWM režimu)."""
        if hasattr(self._driver, "initMotorDriver"):
            self._driver.initMotorDriver()
        elif hasattr(self._driver, "writeTwoRegisters"):
            self._driver.writeTwoRegisters(
                PCA9633_registers.MODE1, 0x00,
                PCA9633_registers.LEDOUT, 0xAA
            )

    # ---------------------------------------------------------
    # Diferenciální kinematika
    # ---------------------------------------------------------

    def setVelocity(self, vMps: float, omegaRad: float) -> None:
        """
        Nastaví rychlost robota pomocí diferenciální kinematiky.

        Args:
            vMps (float): Dopředná rychlost robota v m/s (kladná = vpřed, záporná = vzad).
            omegaRad (float): Úhlová rychlost otáčení v rad/s (kladná = zatáčení vlevo).
        """
        vLeft = vMps - omegaRad * self._halfWheelBase
        vRight = vMps + omegaRad * self._halfWheelBase

        self.left.setLinearSpeed(vLeft)
        self.right.setLinearSpeed(vRight)

    def emergencyShutdown(self) -> None:
        """Bezpečně a okamžitě zastaví všechny motory."""
        log.error("Emergency stop!")
        errors = []

        for side, wheel in self._wheels.items():
            try:
                wheel.stop()
            except Exception as e:
                log.error(f"Chyba při zastavování kola {side}: {e}")
                errors.append(e)

        if errors:
            raise errors[0]

    def setSpeed(self, speeds: dict) -> None:
        """Nastaví PWM rychlosti ze slovníku {DirectionEnum: pwm}."""
        for side, wheel in self._wheels.items():
            wheel.setSpeed(speeds[side])

    def stop(self) -> None:
        """Zastaví oba motory."""
        for wheel in self._wheels.values():
            wheel.stop()

    def update(self) -> None:
        """Periodická aktualizace obou motorů."""
        for wheel in self._wheels.values():
            wheel.update()
