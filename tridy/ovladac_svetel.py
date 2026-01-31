from neopixel import NeoPixel
from board import P0

class OvladacSvetel:
    
    prave_PS = 3
    leve_PS = 0
    bila_slaba = (55,55,55)
    zadna = (0,0,0)

    def __init__(self):
        self.svetla = NeoPixel(P0, 8)
        self.svetla.auto_write = True

    def rozsvitPredniSvetla(self):
        self.svetla[self.prave_PS] = self.bila_slaba
        self.svetla[self.leve_PS] = self.bila_slaba

    def zhasniPredniSvetla(self):
        self.svetla[self.prave_PS] = self.zadna
        self.svetla[self.leve_PS] = self.zadna