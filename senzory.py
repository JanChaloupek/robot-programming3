from picoed import i2c, display

from konstanty import Konstanty

class Senzory:

    def byte_na_bity(self, buffer):
        data_int = int.from_bytes(buffer, "big")
        data_bit_string = bin(data_int)
        return data_bit_string

    #-1 selhalo i2c
    def vycti(self):
        data = ""
        if i2c.try_lock():
            # vycitam senzory
            buffer = bytearray(1)
            i2c.readfrom_into(0x38, buffer)
            i2c.unlock()
            data = self.byte_na_bity(buffer)
            return data
        else: 
            return data

    def cara(self, data_string, senzor):
        if senzor == Konstanty.levy:
            return bool(int(data_string[7]))
        elif senzor == Konstanty.centralni:
            return bool(int(data_string[6]))
        elif senzor == Konstanty.pravy:
            return bool(int(data_string[5]))
        
    def vypis(self, data_string):
        if self.cara(data_string, Konstanty.levy):
            display.pixel(display.width-1,0, 255)
        else:
            display.pixel(display.width-1,0,0)

        if self.cara(data_string, Konstanty.centralni):
            display.pixel(int(display.width/2),0, 255)
        else:
            display.pixel(int(display.width/2),0,0)
        
        if self.cara(data_string, Konstanty.pravy):
            display.pixel(0,0, 255)
        else:
            display.pixel(0,0,0)