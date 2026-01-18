"""
code.py – hlavní program pro robota JoyCar.

Tento soubor:
- vytvoří instanci JoyCarRobota,
- řídí rychlosti motorů v čase,
- používá vestavěné tlačítko A pro ukončení,
- ovládá NeoPixel pásek a LEDku,
- zapisuje logy s časovými značkami,
- PRAVIDELNĚ volá Display.updatePixels(), aby se displej překresloval.
"""

from picoed import button_a, led, display, i2c as pico_i2c
from neopixel import NeoPixel
from board import P0

from joycar import JoyCarRobot, I2C, Display
from utils.period import Period
from utils.log import log


from joycar.robot import JoyCarRobot
from joycar.i2c import I2C
from picoed import i2c as i2c_picoed


def createJoyCarRobot():
    """Vytvoří a vrátí instanci JoyCarRobota."""
    
    # fyzikální parametry robota
    WHEEL_DIAMETER = 0.067
    ROBOT_DIAMETER = 0.15

    # vytvoření I2C wrapperu z JoyCar knihovny (automaticky zamyká a odemká i2c z picoed)
    i2c = I2C(i2c_picoed)

    # vytvoření robota
    return JoyCarRobot(
        i2c=i2c,
        wheelDiameter=WHEEL_DIAMETER,
        wheelBase=ROBOT_DIAMETER
    )



if __name__ == "__main__":
    light = NeoPixel(P0, 8)
    joyCar = None

    try:
        log.info("Program started.")

        nextSpeed = Period(timeout_ms=3000)
        speeds = [
            [150, 150],
            [-150, 100],
            [-100, -150],
            [100, 100],
        ]
        x = 0

        joyCar = createJoyCarRobot()

        while not button_a.is_pressed():
            if nextSpeed.isTime():
                log.flush(max_line=50)
                led.toggle()
                x += 20
                light.fill((x, 0, 0))

                if not speeds:
                    log.info("Last speed reached.")
                    break

                log.info("Next speed.")
                joyCar.wheels.ridePwm(speeds.pop(0))

            joyCar.update()
            Display.updatePixels()   # zajistí překreslování displeje

        log.info("Stopping robot...")
        joyCar.stop()

    except Exception as e:
        log.exception(e)
        if joyCar is not None:
            joyCar.emergencyShutdown()
        raise e

    finally:
        log.info("Program ended.")
        log.flush()

        print("Press button A to exit...")
        while not button_a.is_pressed():
            if joyCar is not None:
                joyCar.update()

        led.off()
        light.fill((0, 0, 0))
        display.clear()
