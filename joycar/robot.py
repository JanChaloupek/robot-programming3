"""
robot.py – hlavní třída JoyCar robota.

Tento modul poskytuje třídu JoyCarRobot, která:
- vytváří senzory,
- vytváří motory,
- propojuje I2C periferie (PCF8574, PCA9633),
- poskytuje jednotné API pro řízení robota.

Použití:
    from joycar.robot import JoyCarRobot
    from joycar.i2c import I2C
    from picoed import i2c as pico_i2c

    robot = JoyCarRobot(I2C(pico_i2c))
    robot.update()
"""

from joycar.i2c import I2C
from joycar.pcf8574 import PCF8574
from joycar.pca9633 import PCA9633
from joycar.sensors import Sensors
from joycar.wheels import Wheels
from joycar.display import Display

class JoyCarRobot:
    """
    Hlavní třída robota JoyCar.

    Atributy:
        sensors (Sensors): Senzory robota.
        wheels (Wheels): Dvojice motorů robota.
    """

    def __init__(self, i2c: I2C, wheelDiameter: float, wheelBase: float) -> None:
        """
        Inicializuje robot JoyCar.

        Args:
            i2c (I2C): I2C wrapper (řeší automatické zamykání)
            wheelDiameter (float): průměr kola v metrech
            wheelBase (float): vzdálenost mezi koly v metrech
        """
        pcf8574 = PCF8574(i2c)
        pca9633 = PCA9633(i2c)

        self.sensors = Sensors(pcf8574)
        self.wheels = Wheels(pca9633, wheelDiameter, wheelBase)

    def update(self) -> None:
        """Periodická aktualizace robota (senzory + motory)."""
        self.sensors.update()
        self.wheels.update()
        Display.updatePixels()        

    def stop(self) -> None:
        """Zastaví robota (oba motory)."""
        self.wheels.stop()

    def emergencyShutdown(self) -> None:
        """Bezpečně zastaví robota (nouzové zastavení)."""
        self.wheels.emergencyShutdown()

def createTestWheels():
    """Vytvoří a vrátí testovací instanci Wheels pro JoyCar robota."""
    from picoed import i2c as i2c_picoed
    WHEEL_DIAMETER = 0.06  # v metrech
    ROBOT_DIAMETER = 0.12  # v metrech

    # vytvoření I2C wrapperu z JoyCar knihovny (automaticky zamyká a odemká i2c z picoed)
    i2c = I2C(i2c_picoed)

    # vytvoření kol
    return Wheels(
        pca9633=PCA9633(i2c),
        diameter=WHEEL_DIAMETER,
        wheelBase=ROBOT_DIAMETER
    )