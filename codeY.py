from picoed import button_b, button_a
from time import sleep

from robot import Robot
from konstanty import Konstanty

# -1 error v inicializace robotast_start
def main():
    muj_robot = Robot()
    muj_robot.inicializace()
    #ceka 2ms na stabilizaci i2c, to je s rezervou vic nez pozadovanych 500us
    sleep(0.002)   
    muj_robot.stop()

    if not muj_robot.zinicializovano:
        print("Robot se nezinicializoval")
        return -1
    
    aktualni_stav = Konstanty.st_vycti_senzory

    # while not button_a.was_pressed():
    #    muj_robot.aktualizuj_se()
        
    #    data = muj_robot.senzory.vycti()
    #    muj_robot.senzory.vypis(data)
    #    sleep(0.005)
        
    #testovani jizdy vzad a dopredu
    muj_robot.pravy_motor.jed_pwm(Konstanty.dozadu, 130)
    muj_robot.pravy_motor.jed_pwm(Konstanty.dopredu, 130)
    
    while not button_b.was_pressed():
        muj_robot.aktualizuj_se()

        if aktualni_stav == Konstanty.st_vycti_senzory:
            data = muj_robot.senzory.vycti()
            muj_robot.senzory.vypis(data)
            aktualni_stav = Konstanty.st_reaguj_na_caru
        
        if aktualni_stav == Konstanty.st_reaguj_na_caru:
            if muj_robot.senzory.cara(data, Konstanty.levy):
                muj_robot.zatoc_doleva()
            elif muj_robot.senzory.cara(data, Konstanty.pravy):
                muj_robot.zatoc_doprava()
            
            aktualni_stav = Konstanty.st_vycti_senzory
        
        sleep(0.005)
    
    muj_robot.stop()

if __name__ == "__main__":
    main()