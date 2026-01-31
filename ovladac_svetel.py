from neopixel import NeoPixel
from board import P0
from casovac import Casovac

class OvladacSvetel:
    
    prave_PS = 3
    leve_PS = 0
    bila_slaba = (55,55,55)
    zadna = (0,0,0)

    def __init__(self):
        self.svetla = NeoPixel(P0, 8)
        self.svetla.auto_write = True
        self.rozsviceno = False
        self._casovac_blikani = Casovac(spustit=True)

    def rozsvitPredniSvetla(self):
        self.rozsviceno = True
        self.svetla[self.prave_PS] = self.bila_slaba
        self.svetla[self.leve_PS] = self.bila_slaba

    def zhasniPredniSvetla(self):
        self.rozsviceno = False
        self.svetla[self.prave_PS] = self.zadna
        self.svetla[self.leve_PS] = self.zadna

    def blikni(self):
        if self.rozsviceno:
            self.zhasniPredniSvetla()
        else:
            self.rozsvitPredniSvetla()

    def aktualizuj_se(self):
        if self._casovac_blikani.vypsel_cas_cekani(500):
            self.blikni()
            self._casovac_blikani.start()
