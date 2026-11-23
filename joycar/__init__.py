"""
joycar – modulární implementace robota JoyCar.

Studentům:
- Tento balík obsahuje vše potřebné pro ovládání robota.
- JoyCarRobot je hlavní třída (fasáda), která propojuje displej, senzory, motory a světla.
- Podporuje přepínání budičů motoru (PCA9633 pro 0–255 nebo PCA9685 pro 0–4095).
- Podporuje přepínání 2 až 6 senzorů čáry pro různé verze podvozku.
- Podporuje textový LCD displej (HD44780 na I2C), který lze snadno zapínat a vypínat.
- sm obsahuje stavový automat a plánovač CPU pro neblokující chování.
- lights obsahuje kompletní ovládání světel (NeoPixel páska na P0).
- navigation obsahuje řízení misí a průjezdu křižovatkami.
"""

from typing import Any, Optional
from picoed import i2c as pico_i2c

from .display import Display, display
from .battery import battery_voltage
from .i2c import I2C
from .pcf8574 import PCF8574
from .pca9633 import PCA9633, PCA9633_registers
from .pca9685 import PCA9685, PCA9685_registers
from .calibration import CalibrateFactors
from .lcd import TextDisplay
from .robot import JoyCarRobot
from .sensors import Sensors, LineSituationEnum, CrossRoadType
from .line_trackers import (
    BaseLineTracker,
    LineTracker2,
    LineTracker3,
    LineTracker4,
    LineTracker5,
    LineTracker6,
    createLineTracker,
)
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


def createJoyCarRobot(line_sensors: int = 3,
                      driver: Any = None,
                      calibration: Optional[CalibrateFactors] = None,
                      lcd_enabled: bool = False) -> JoyCarRobot:
    """
    Vytvoří a nakonfiguruje instanci robota JoyCar.

    Args:
        line_sensors (int): Počet senzorů čáry (2, 3, 4, 5 nebo 6). Výchozí: 3.
        driver (Any): Budič motorů (PCA9633, PCA9685 nebo řetězec 'PCA9685').
        calibration (Optional[CalibrateFactors]): Kalibrační hodnoty motorů.
        lcd_enabled (bool): Zda má být textový LCD displej aktivní (výchozí False).
    """
    return JoyCarRobot(
        I2C(pico_i2c),
        line_sensors=line_sensors,
        driver=driver,
        calibration=calibration,
        lcd_enabled=lcd_enabled
    )
