"""
wheels.py – řízení obou motorů JoyCar robota.

Tento modul poskytuje třídu Wheels, která:
- obsahuje dva motory (levý + pravý),
- inicializuje PCA9633,
- umožňuje řízení obou motorů současně,
- podporuje diferenciální kinematiku (v, omega).
"""

from joycar import wheel
from joycar.wheel import Wheel
from joycar.direction import DirectionEnum
from joycar.pca9633 import PCA9633, PCA9633_registers
from utils.log import log


class Wheels:
    """Řídí dvojici motorů (levý + pravý)."""

    def __init__(self, pca9633: PCA9633, diameter: float, wheelBase: float) -> None:
        """
        Inicializuje dvojici kol a parametry podvozku.

        Args:
            pca9633 (PCA9633): driver motorů
            diameter (float): průměr kol v metrech
            wheelBase (float): vzdálenost mezi koly v metrech
        """
        self._pca9633 = pca9633

        # uložíme polovinu vzdálenosti mezi koly (pro diferenciální kinematiku)
        self._halfWheelBase = wheelBase / 2

        self._wheels = {
            DirectionEnum.LEFT: Wheel(DirectionEnum.LEFT, pca9633, diameter),
            DirectionEnum.RIGHT: Wheel(DirectionEnum.RIGHT, pca9633, diameter),
        }

        self._initMotorDriver()

    @property
    def left(self) -> Wheel:
        return self._wheels[DirectionEnum.LEFT]

    @property
    def right(self) -> Wheel:
        return self._wheels[DirectionEnum.RIGHT]

    def _initMotorDriver(self) -> None:
        """Inicializuje PCA9633 driver."""
        self._pca9633.writeTwoRegisters(
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
            vMps (float): dopředná rychlost robota v m/s
            omegaRad (float): úhlová rychlost v rad/s (kladná = zatáčení vlevo)
        """

        vLeft = vMps - omegaRad * self._halfWheelBase
        vRight = vMps + omegaRad * self._halfWheelBase

        # aplikace rychlostí
        self.left.setLinearSpeed(vLeft)
        self.right.setLinearSpeed(vRight)

    # ---------------------------------------------------------

    def emergencyShutdown(self) -> None:
        """Bezpečně zastaví všechny motory, ale chyby propaguje dál."""
        log.error("Emergency stop!")

        errors = []

        for side, wheel in self._wheels.items():
            try:
                wheel.stop()
            except Exception as e:
                log.error(f"Chyba při zastavování kola {side}: {e}")
                errors.append(e)

        if errors:
            # propagujeme první chybu (nebo můžeš vytvořit vlastní)
            raise errors[0]

    def setSpeed(self, speeds: dict) -> None:
        for side, wheel in self._wheels.items():
            wheel.setSpeed(speeds[side])

    def stop(self) -> None:
        """Zastaví oba motory."""
        for wheel in self._wheels.values():
            wheel.stop()

    def update(self) -> None:
        """Periodicky aktualizuje oba motory."""
        for wheel in self._wheels.values():
            wheel.update()

