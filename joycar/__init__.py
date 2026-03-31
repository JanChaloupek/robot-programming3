"""
joycar – modulární implementace robota JoyCar.

Studentům:
- Tento balík obsahuje vše potřebné pro ovládání robota.
- JoyCarRobot je hlavní třída, která propojuje displej, senzory a motory.
"""

from picoed import i2c as pico_i2c

from .display import Display, display
from .battery import battery_voltage
from .i2c import I2C
from .pcf8574 import PCF8574
from .pca9633 import PCA9633, PCA9633_registers
from .robot import JoyCarRobot
from .sensors import Sensors
from .wheel import Wheel, DirectionEnum
from .wheels import Wheels


def createJoyCarRobot() -> JoyCarRobot:
    """Vytvoří a vrátí instanci JoyCarRobota."""
    return JoyCarRobot(I2C(pico_i2c))
