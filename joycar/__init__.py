"""
joycar – modulární implementace robota JoyCar.

Studentům:
- Tento balík obsahuje vše potřebné pro ovládání robota.
- JoyCarRobot je hlavní třída, která propojuje displej, senzory a motory.
- sm obsahuje stavový automat a plánovač CPU pro neblokující chování.
- lights obsahuje kompletní ovládání světel (NeoPixel páska na P0).
- navigation obsahuje řízení misí a průjezdu křižovatkami.
"""

from picoed import i2c as pico_i2c

from .display import Display, display
from .battery import battery_voltage
from .i2c import I2C
from .pcf8574 import PCF8574
from .pca9633 import PCA9633, PCA9633_registers
from .robot import JoyCarRobot
from .sensors import Sensors, LineSituationEnum, CrossRoadType
from .wheel import Wheel, DirectionEnum
from .wheels import Wheels
from .sm import CPU, Task, Step, AbstractSM
from .lights import LightsControl, Indicator, BeamsEnum
from .navigation import Commands, CrossRoadsSM
from .sound import (
    HornController,
    HonkData,
    honk_data,
    tutu,
    warningShort,
    warningLong,
    hello,
    panic,
    brzdeni,
)
from utils.log import log, LogLevelEnum, Log


def createJoyCarRobot() -> JoyCarRobot:
    """Vytvoří a vrátí instanci JoyCarRobota."""
    return JoyCarRobot(I2C(pico_i2c))
