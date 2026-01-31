from picoed import i2c 
from konstanty import Konstanty
from casovac import Casovac

class Motor:

    def __init__(self, strana):
        self.strana = strana
        self._casovac = Casovac(spustit=False)
        # stojime
        self.rychlost = 0
        self._naposledy_odeslana_rychlost = 0
        # vyber kanalů podle strany
        if self.strana == Konstanty.pravy:
            self.kanal_dozadu = 0x02        # adresa registru PWM0
            self.kanal_dopredu = 0x03       # adresa registru PWM1
        elif self.strana == Konstanty.levy:
            self.kanal_dozadu = 0x04        # adresa registru PWM2
            self.kanal_dopredu = 0x05       # adresa registru PWM3
        else:
            raise ValueError("Neplatna strana motoru")

    """ Odesle pwm na i2c
        kanal_on: kanal pro zapnuti
        kanal_off: kanal pro vypnuti
        return: 0 vse ok, -1 chyba i2c
    """
    def _odesli_pwm(self, kanal_on, kanal_off, rychlost):
        if not i2c.try_lock():
            print("Nepodarilo se zamknout i2c")
            return -1
        try:
            i2c.writeto(0x70,  bytes([kanal_off, 0]))
            i2c.writeto(0x70, bytes([kanal_on, rychlost]))
        finally:
            i2c.unlock()
        return 0

    """ Vrati True, pokud doslo ke zmene smeru motoru """
    def nastala_zmena_smeru(self):
        return (self.rychlost * self._naposledy_odeslana_rychlost) < 0

    """ Odesle pwm bezpecne s ohledem na zmenu smeru"""
    def odesilej_rychlost_bezpecne(self):
        if self.rychlost == self._naposledy_odeslana_rychlost:
            # zadna zmena rychlosti (namam duvod odesilat znovu)
            return

        if self.nastala_zmena_smeru():
            # zastavime pred zmenou smeru
            self._odesli_pwm(self.kanal_dopredu, self.kanal_dozadu, 0)
            # naposledy odeslana rychlost je nula
            self._naposledy_odeslana_rychlost = 0
            # spustime cekani na reverz
            self._casovac.start()

        if self._casovac.casovac_bezi():
             # cekame 500ms po zmene smeru
            if not self._casovac.vypsel_cas_cekani(500): 
                # jeste nevyprsel cas, musime jeste pockat 
                return 0  
            # uz uplynul cas, zastavime casovac a muzeme odeslat novou rychlost
            self._casovac.stop()

        # odesleme novou rychlost
        if self.rychlost > 0:
            self._odesli_pwm(self.kanal_dopredu, self.kanal_dozadu, self.rychlost)
        else:
            self._odesli_pwm(self.kanal_dozadu, self.kanal_dopredu, -self.rychlost)
        # a ulozime si novou puvodni rychlost
        self._naposledy_odeslana_rychlost = self.rychlost

    # 0 vse ok
    # -2 spatny smer
    # -3 spatna rychlost
    def jed_pwm(self, smer, rychlost):
        rychlost = int(rychlost)
        if rychlost < 0 or rychlost > 255:
            return -3
        if smer != Konstanty.dopredu and smer != Konstanty.dozadu:
            return -2

        if smer == Konstanty.dopredu:
            self.rychlost = rychlost
        else:
            self.rychlost = -rychlost
        self.odesilej_rychlost_bezpecne()
        return 0

    """ Aktualizuje motor (odesila rychlost pokud muze a ma co) """
    def aktualizuj_se(self):
        self.odesilej_rychlost_bezpecne()