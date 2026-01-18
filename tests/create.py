"""create.py – pomocná funkce pro vytváření Wheels objektu v testech."""

from joycar.i2c import I2C
from joycar.pca9633 import PCA9633
from joycar.pcf8574 import PCF8574
from joycar.sensors import Sensors
from joycar.wheels import Wheels
from joycar.wheel import Wheel

def createWheels(hw_i2c) -> Wheels:
    return Wheels(PCA9633(I2C(hw_i2c)), diameter=0.06, wheelBase=0.12)

def createWheel(hw_i2c, side) -> Wheel:
    return Wheel(side, PCA9633(I2C(hw_i2c)), diameter=0.06)

def createSensors(hw_i2c):
    return Sensors(PCF8574(I2C(hw_i2c)))

def createRobot(hw_i2c):
    from joycar.robot import JoyCarRobot
    return JoyCarRobot(I2C(hw_i2c), wheelDiameter=0.06, wheelBase=0.12)