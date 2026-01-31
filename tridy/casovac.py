from adafruit_ticks import ticks_ms, ticks_diff

""" Třída Casovac pro měření uplynulého času. """
class Casovac:
    """ Inicializace casovace """
    def __init__(self, spustit=True):
        self.start_time = None
        if spustit:
            self.start()

    """ Spusti casovac """
    def start(self):
        # zaznamena aktualni cas
        self.start_time = ticks_ms()

    """ Zastavi casovac """
    def stop(self):
        self.start_time = None

    """ Vrati True, pokud casovac bezi """
    def casovac_bezi(self):
        return self.start_time is not None

    """ Vrati True, pokud uplynul dany cas od startu casovace """
    def vypsel_cas_cekani(self, cekame_ms):
        if self.start_time is None:
            return False
        # ziska aktualni cas
        aktualni_cas = ticks_ms()
        return ticks_diff(aktualni_cas, self.start_time) >= cekame_ms
