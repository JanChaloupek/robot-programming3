"""
sound.py – Zvukový subsystém (bzučák / klakson) robota JoyCar.

Vzorový výukový modul pro studenty:
-----------------------------------
Tento modul ukazuje, jak generovat zvuky, tóny a melodie na robotovi
zcela NEBLOKUJÍCÍM způsobem v architektuře Superloop.

Proč v robotice NESMÍME použít sleep() pro melodie:
---------------------------------------------------
V začátečnických programech se tóny obvykle hrají takto:
    picoed.music.pitch(440, duration=1000)   # ZABLOKUJE běh na 1 sekundu!
nebo:
    buzzer.duty_cycle = 32768
    time.sleep(0.5)                          # ZABLOKUJE běh na 500 ms!
    buzzer.duty_cycle = 0

Když robot jede po čáře rychlostí 0.3 m/s (30 cm za sekundu) a potká křižovatku,
blokující čekání 500 ms způsobí, že robot ujede 15 centimetrů „poslepu“. Během
té doby nemůže číst infračervené senzory čáry, nemůže reagovat na překážku
a spolehlivě havaruje nebo sjede z trati!

Více podrobností o zákazu sleep():
- file:///C:/Projekty/pomucky/superloop.md (metafora šéfkuchaře a orchestru)
- file:///C:/Projekty/pomucky/sleep.md (rozdíl v blokování MicroPython vs CircuitPython)
- file:///C:/Projekty/pomucky/compare_tick_function.md (proč používáme adafruit_ticks)

Jak funguje neblokující HornController:
--------------------------------------
1. Třída HonkData definuje sekvenci frekvencí (Hz), délek tónů (ms) a mezer (ms).
2. Metoda play(honk_data) pouze nastaví frekvenci prvního tónu a spustí časovač Period.
   Metoda okamžitě skončí a nezdrží superloop ani o milisekundu.
3. V každém cyklu hlavní smyčky robot zavolá horn.update():
   - Časovač Period neblokujícím způsobem testuje, zda uplynul čas tónu.
   - Jakmile tón skončí, bzučák se ztiší (duty_cycle = 0) a spustí se časovač mezery.
   - Po uplynutí mezery se přejde na další tón v melodii.
   - Po dohrání všech tónů se stav přepne na neaktivní (playing = False).
"""

from __future__ import annotations

try:
    import board
    import pwmio
except ImportError:
    board = None
    pwmio = None

from utils.period import Period


class HonkData:
    """
    Datová třída reprezentující sekvenci tónů a mezer pro zvukovou znělku.

    Atributy:
        tones (list[int]): Frekvence tónů v Hz (např. 1000 Hz).
        durations (list[int]): Délka trvání jednotlivých tónů v ms.
        pauses (list[int]): Délka ticha (mezery) za každým tónem v ms.
    """

    def __init__(self, tones: list[int], durations: list[int], pauses: list[int]) -> None:
        """
        Inicializuje sekvenci tónů.

        Args:
            tones: Seznam frekvencí tónů v Hz.
            durations: Seznam délek jednotlivých tónů v milisekundách.
            pauses: Seznam délek mezer mezi tóny v milisekundách.

        Raises:
            ValueError: Pokud je libovolný ze seznamů prázdný nebo nemají stejnou délku.
        """
        if not tones or not durations or not pauses:
            raise ValueError("Sekvence troubení musí obsahovat alespoň jeden tón, délku a pauzu!")
        if len(tones) != len(durations) or len(tones) != len(pauses):
            raise ValueError("Počet tónů, délek a mezer v sekvenci musí být shodný!")

        self.tones = list(tones)
        self.durations = list(durations)
        self.pauses = list(pauses)

    def __len__(self) -> int:
        return len(self.tones)


# -----------------------------------------------------------------------------
# Předdefinované znělky přenesené a optimalizované z 2-SW_GIT
# -----------------------------------------------------------------------------

# Výchozí klakson – krátké zatroubení
honk_data = HonkData(
    tones=[1000, 1200, 900, 1000, 1100],
    durations=[150, 200, 100, 250, 180],
    pauses=[50, 80, 60, 100, 90]
)

# Klasické dvojité zatroubení "tu-tu"
tutu = HonkData(
    tones=[1000, 1000],
    durations=[500, 700],
    pauses=[50, 1]
)

# Krátké výstražné pípnutí
warningShort = HonkData(
    tones=[1000, 1200],
    durations=[150, 200],
    pauses=[100, 100]
)

# Dlouhé varovné pípnutí
warningLong = HonkData(
    tones=[800, 900, 800],
    durations=[400, 500, 600],
    pauses=[150, 150, 200]
)

# Melodie při zapnutí / startu robota
hello = HonkData(
    tones=[1000, 1300, 1500, 1300, 1000],
    durations=[200, 150, 180, 150, 200],
    pauses=[100, 80, 90, 80, 100]
)

# Poplašná siréna při nouzovém zastavení / ztrátě čáry
panic = HonkData(
    tones=[1000, 1100, 1200, 1300, 1400],
    durations=[300, 300, 300, 300, 300],
    pauses=[50, 50, 50, 50, 50]
)

# Zvuk zpomalování a brzdění před křižovatkou (klesající vibrace)
brzdeni = HonkData(
    tones=[5000, 4000, 3000, 2500, 2000, 1500, 1000],
    durations=[100, 120, 140, 160, 180, 200, 250],
    pauses=[20, 40, 60, 80, 100, 120, 150]
)


class HornController:
    """
    Neblokující kontrolér bzučáku / klaksonu.

    Řídí PWM výstup bzučáku pomocí časovače Period. Umožňuje přehrávat
    vícekrokové melodie a zvukové sekvence na pozadí, aniž by zdržoval
    hlavní smyčku superloopu robota.
    """

    VOLUME_DUTY_CYCLE = 32768  # 50 % střída pro čistý obdélníkový akustický signál

    def __init__(self, pwm_out=None, pin=None) -> None:
        """
        Args:
            pwm_out: Volitelný existující PWMOut objekt (nebo testovací fake).
            pin: Pin připojený k bzučáku (např. board.BUZZER nebo board.P16).
                 Použije se jen pokud není zadán pwm_out.
        """
        self._pwm = pwm_out
        self._pin = pin
        self._owns_pwm = False

        if self._pwm is None and pin is not None and pwmio is not None:
            try:
                self._pwm = pwmio.PWMOut(pin, frequency=1000, duty_cycle=0, variable_frequency=True)
                self._owns_pwm = True
            except Exception:
                self._pwm = None

        self.data: HonkData | None = None
        self.index = 0
        self.period: Period | None = None
        self.is_honking = False
        self.playing = False

    @property
    def is_playing(self) -> bool:
        """Vrací True, pokud právě probíhá přehrávání melodie."""
        return self.playing

    def play(self, honk_data: HonkData) -> None:
        """
        Spustí přehrávání zadané melodie od začátku.

        Operace je zcela neblokující – pouze inicializuje stav a časovač.
        """
        if not honk_data:
            return

        self.data = honk_data
        self.index = 0
        self.is_honking = True
        self.playing = True

        if self.period is None:
            self.period = Period(timeout_ms=self.data.durations[self.index])
        else:
            self.period.startTimer(timeout_ms=self.data.durations[self.index])

        self._apply_tone()

    # Alias pro zpětnou kompatibilitu s 2-SW_GIT
    play_honk = play

    def stop(self) -> None:
        """Okamžitě zastaví přehrávání a ztiší bzučák."""
        self.playing = False
        self.is_honking = False
        self._silence()
        if self.period:
            self.period.stopTimer()

    def _apply_tone(self) -> None:
        """Nastaví frekvenci a zapne akustický signál."""
        if self._pwm is not None and self.data is not None:
            freq = self.data.tones[self.index]
            self._pwm.frequency = freq
            self._pwm.duty_cycle = self.VOLUME_DUTY_CYCLE

    def _silence(self) -> None:
        """Vypne buzení bzučáku (nastaví střídu na 0)."""
        if self._pwm is not None:
            self._pwm.duty_cycle = 0

    def update(self) -> None:
        """
        Krokování přehrávače – volá se periodicky v každém tiku superloopu.

        Pokud vypršel časovač aktuálního tónu, přepne se na pauzu.
        Pokud vypršela pauza, přepne se na další tón v pořadí.
        """
        if not self.playing or self.period is None or self.data is None:
            return

        if self.period.isTime():
            if self.is_honking:
                # Tón skončil -> začíná pauza
                self._silence()
                self.is_honking = False
                pause_ms = self.data.pauses[self.index]
                self.period.startTimer(timeout_ms=pause_ms)
            else:
                # Pauza skončila -> posun na další tón
                self.index += 1
                if self.index >= len(self.data.tones):
                    # Došli jsme na konec melodie -> ukončíme přehrávání
                    self.stop()
                    return

                # Spuštění dalšího tónu
                self.is_honking = True
                self._apply_tone()
                duration_ms = self.data.durations[self.index]
                self.period.startTimer(timeout_ms=duration_ms)
