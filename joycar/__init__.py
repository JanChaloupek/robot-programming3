"""
joycar – modulární implementace robota JoyCar.

Tento balík obsahuje:
- JoyCarRobot (hlavní třída robota),
- Display (ovladač LED displeje),
- I2C wrapper,
- ovladače PCF8574 a PCA9633,
- senzory,
- motory (Wheel, Wheels).

Použití:
    from joycar import JoyCarRobot, I2C
"""
from picoed import i2c as pico_i2c
from .display import Display
from .i2c import I2C
from .pcf8574 import PCF8574
from .pca9633 import PCA9633, PCA9633_registers
from .robot import JoyCarRobot
from .sensors import Sensors
from .wheel import Wheel, DirectionEnum
from .wheels import Wheels


def createJoyCarRobot() -> JoyCarRobot:
    """
    Vytvoří a vrátí instanci JoyCarRobota.

    Používá:
        - I2C wrapper nad pico_i2c,
        - JoyCarRobot jako hlavní třídu robota.
    """
    return JoyCarRobot(I2C(pico_i2c))

