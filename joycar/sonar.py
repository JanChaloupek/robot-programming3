"""
sonar.py – Ultrazvukový dálkoměr HC-SR04 pro měření vzdálenosti od překážek.

Vzorový výukový modul pro studenty robota JoyCar:
------------------------------------------------
Tento modul zajišťuje bezpečné a neblokující měření vzdálenosti k překážkám
pomocí ultrazvukového senzoru HC-SR04 (nebo HC-SR04P na 3.3V).

Základní fyzikální princip měření:
----------------------------------
1. Mikrokontrolér vyšle na pin Trigger krátký impulz (10 mikrosekund).
2. Vysílač sonaru vyšle 8 ultrazvukových vln o frekvenci 40 kHz.
3. Vlna se šíří vzduchem rychlostí zvuku (cca 343 m/s při pokojové teplotě).
4. Po odrazu od překážky zachytí přijímač odezvu a na pinu Echo nastaví log. 1
   po dobu odpovídající celkové dráze tam a zpět (čas letu pulzu t).
5. Vzdálenost k překážce se spočítá podle vzorce:
       vzdalenost = (t * rychlost_zvuku) / 2

Základní SI jednotky:
---------------------
V celém kurzu striktně používáme základní jednotky SI, tedy METRY [m].
- Všechny vzdálenosti se zadávají a vrací v metrech (např. 0.20 m).
- Rychlost zvuku je 343 m/s.

Neblokující řízení (Superloop):
--------------------------------
Měření neblokuje hlavní smyčku robota funkcí sleep(). Třída využívá časovač
Period a měří s nastavenou periodou (výchozí 60 ms = cca 16 Hz).
Naměřené hodnoty jsou vyhlazovány klouzavým průměrem pro eliminaci odrazů.
"""

from typing import Optional, Any
from utils.period import Period
from utils.log import log

try:
    import board
    import digitalio
except ImportError:
    from _fake import board, digitalio


class Sonar:
    """
    Ovladač ultrazvukového senzoru HC-SR04.

    Vlastnosti:
    - Všechny vzdálenosti jsou výhradně v metrech (m).
    - Možnost snadného zapnutí a vypnutí (enable/disable), aby nezatěžoval sběrnici,
      pokud není modul fyzicky osazen.
    - Klouzavý vyhlazovací filtr pro odstranění chyb měření a falešných odrazů.
    """

    SPEED_OF_SOUND = 343.0   # Rychlost zvuku v m/s při 20 °C
    MAX_DISTANCE_M = 3.0     # Maximální měřitelný dosah v metrech
    FILTER_SIZE = 3          # Počet vzorků pro klouzavý průměr

    def __init__(self,
                 trigger_pin: Any = None,
                 echo_pin: Any = None,
                 timeout_ms: int = 60,
                 enabled: bool = False) -> None:
        """
        Inicializace ultrazvukového dálkoměru.

        Args:
            trigger_pin: Pin mikrokontroléru pro vysílací impulz (výchozí board.P8).
            echo_pin: Pin mikrokontroléru pro měření odrazu (výchozí board.P12).
            timeout_ms: Perioda měření v ms (výchozí 60 ms).
            enabled: Zda je sonar aktivní (výchozí False).
        """
        if trigger_pin is None and hasattr(board, "P8"):
            trigger_pin = board.P8
        if echo_pin is None and hasattr(board, "P12"):
            echo_pin = board.P12

        self._trigger_pin = trigger_pin
        self._echo_pin = echo_pin
        self._period = Period(timeout_ms=timeout_ms)
        self._enabled = enabled
        self._first_run = True

        self._distance: Optional[float] = None
        self._history: list[float] = []
        self._consecutive_timeouts = 0
        self._mock_distance: Optional[float] = None

        self._hw_driver = None
        if self._enabled:
            self._initHardware()

    # -------------------------------------------------------------------------
    # Zapínání a vypínání sonaru
    # -------------------------------------------------------------------------

    @property
    def is_enabled(self) -> bool:
        """Vrací True, pokud je měření aktivní."""
        return self._enabled

    def enable(self) -> None:
        """Zapne sonar a aktivuje periodické měření."""
        if not self._enabled:
            self._enabled = True
            self._first_run = True
            self._initHardware()
            log.info("Sonar: zapnut.")

    def disable(self) -> None:
        """Vypne sonar, pozastaví měření a resetuje vyrovnávací paměť."""
        if self._enabled:
            self._enabled = False
            self._first_run = False
            self._distance = None
            self._history.clear()
            self._consecutive_timeouts = 0
            log.info("Sonar: vypnut.")

    # -------------------------------------------------------------------------
    # Čtení vzdálenosti a rozhodování
    # -------------------------------------------------------------------------

    @property
    def distance(self) -> Optional[float]:
        """
        Poslední změřená vyhlazená vzdálenost k překážce v METRECH.

        Returns:
            float: Vzdálenost v metrech (např. 0.25 m).
            None: Pokud je sonar vypnutý, překážka je mimo dosah, nebo došlo k chybě.
        """
        if not self._enabled:
            return None
        return self._distance

    def is_obstacle_near(self, threshold_m: float = 0.20) -> bool:
        """
        Rychlý dotaz, zda je před robotem překážka blíže než zadaný limit.

        Args:
            threshold_m: Mezní vzdálenost v metrech (výchozí 0.20 m).

        Returns:
            bool: True pokud je překážka blíže než threshold_m, jinak False.
        """
        d = self.distance
        if d is None:
            return False
        return d < threshold_m

    # -------------------------------------------------------------------------
    # Testovací simulace (Mocking)
    # -------------------------------------------------------------------------

    def set_mock_distance(self, distance_m: Optional[float]) -> None:
        """
        Nastaví simulovanou vzdálenost pro testování na PC bez fyzického senzoru.

        Args:
            distance_m: Vzdálenost v metrech nebo None (pro simulaci timeoutu / volného prostoru).
        """
        self._mock_distance = distance_m

    # -------------------------------------------------------------------------
    # Interní měření a Superloop aktualizace
    # -------------------------------------------------------------------------

    def _initHardware(self) -> None:
        """Inicializuje hardwarové piny nebo knihovnu HC-SR04 v CircuitPythonu."""
        try:
            import adafruit_hcsr04
            self._hw_driver = adafruit_hcsr04.HCSR04(
                trigger_pin=self._trigger_pin,
                echo_pin=self._echo_pin
            )
        except Exception:
            # Fallback pro PC simulátor nebo prostředí bez adafruit_hcsr04
            self._hw_driver = None

    def _readRawDistance(self) -> Optional[float]:
        """Provede jedno fyzické měření a vrátí surovou vzdálenost v metrech."""
        # 1. Simulovaný mock pro unit testy
        if self._mock_distance is not None or (hasattr(self, "_mock_distance") and self._mock_distance is None and self._hw_driver is None):
            return self._mock_distance

        # 2. Reálný CircuitPython driver
        if self._hw_driver is not None:
            try:
                # Knihovna adafruit_hcsr04 vrací hodnotu v cm; ihned ji převedeme na metry (základní jednotka SI)
                raw_cm = self._hw_driver.distance
                distance_m = round(raw_cm / 100.0, 4)
                if distance_m <= self.MAX_DISTANCE_M:
                    return distance_m
                return None
            except RuntimeError:
                # Běžný stav při timeoutu (překážka je mimo dosah paprsku)
                return None
            except Exception as e:
                log.debug(f"Sonar: Chyba čtení: {e}")
                return None

        return None

    def measure(self) -> Optional[float]:
        """
        Provede měření, aplikuje vyhlazovací filtr a aktualizuje stav.
        Metoda je volána automaticky v update(), ale lze ji volat i přímo.
        """
        if not self._enabled:
            return None

        raw = self._readRawDistance()

        if raw is not None and 0.0 <= raw <= self.MAX_DISTANCE_M:
            self._consecutive_timeouts = 0
            self._history.append(raw)
            if len(self._history) > self.FILTER_SIZE:
                self._history.pop(0)
            self._distance = round(sum(self._history) / len(self._history), 4)
        else:
            self._consecutive_timeouts += 1
            # Po několika po sobě jdoucích timeoutech považujeme prostor za volný
            if self._consecutive_timeouts >= self.FILTER_SIZE:
                self._distance = None
                self._history.clear()

        return self._distance

    def update(self) -> None:
        """
        Periodická aktualizace v hlavní smyčce robota (Superloop).
        Měření probíhá pouze tehdy, když uplyne nastavená perioda (např. 60 ms).
        """
        if self._enabled and (self._first_run or self._period.isTime()):
            if self._first_run:
                self._first_run = False
                self._period.restart()
            self.measure()
