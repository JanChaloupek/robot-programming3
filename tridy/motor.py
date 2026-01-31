from picoed import i2c 

from konstanty import Konstanty

class Motor:

    def __init__(self, strana):
        self.strana = strana
  
    # 0 vse ok
    # -1 spatna strana motoru
    # -2 spatny smer
    # -3 spatna rychlost
    def jed_pwm(self, smer, rychlost):

        rychlost = int(rychlost)
        if rychlost < 0 or rychlost > 255:
            return -3
    
        kanal_on = ""
        kanal_off = ""

        if self.strana == Konstanty.levy:
            if smer == Konstanty.dopredu:
                kanal_on = b"\x05"
                kanal_off = b"\x04"
            elif smer == Konstanty.dozadu:
                kanal_on = b"\x04"
                kanal_off = b"\x05"
            else:
                return -2
        elif self.strana == Konstanty.pravy:
            if smer == Konstanty.dopredu:
                kanal_on = b"\x03"
                kanal_off = b"\x02"
            elif smer == Konstanty.dozadu:
                kanal_on = b"\x02"
                kanal_off = b"\x03"
            else:
                return -2
        else:           
            return -1 


        if i2c.try_lock():
            i2c.writeto(0x70, kanal_off + bytes([0]))
            i2c.writeto(0x70, kanal_on + bytes([rychlost]))
            i2c.unlock()
        else:
            print("Nepodarilo se zamknout i2c") 
