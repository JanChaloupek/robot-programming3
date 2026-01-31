from picoed import i2c
from time import sleep

from motor import Motor
from konstanty import Konstanty
from senzory import Senzory

class Robot:

    zinicializovano = False

    def __init__(self):
        self.levy_motor = Motor(Konstanty.levy)
        self.pravy_motor = Motor(Konstanty.pravy)
        self.senzory = Senzory()

    
    def inicializace(self):

        if i2c.try_lock():
            #inicializovace cipu motoru
            i2c.writeto(0x70, b'\x00\x01')
            i2c.writeto(0x70, b'\xE8\xAA')
            self.zinicializovano = True
            i2c.unlock()
            return 0
        else:
            print("Nepodarilo se zamknout i2c") 
            return -1

        sleep(0.1)
    
    def zatoc_doleva(self):
        self.levy_motor.jed_pwm(Konstanty.dopredu, 0)
        self.pravy_motor.jed_pwm(Konstanty.dopredu, 127)
    
    def zatoc_doprava(self):
        self.levy_motor.jed_pwm(Konstanty.dopredu, 127)
        self.pravy_motor.jed_pwm(Konstanty.dopredu, 0)
    
    def stop(self):
        self.levy_motor.jed_pwm(Konstanty.dopredu, 0)
        self.pravy_motor.jed_pwm(Konstanty.dopredu, 0)
