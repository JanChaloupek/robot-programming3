from typing import Optional


__all__ = ["display", "Display"]


class Display:
    """
    Ovladač 17×7 LED displeje na desce pico:ed / JoyCar.

    Tato třída poskytuje:
    - rychlé vykreslování ikon a čísel,
    - optimalizovaný přenos přes I²C (jediný blok 145 bajtů),
    - předpočítané indexy pro ikony (ultra-fast bitmapy),
    - zpětně kompatibilní API (iconA/B/C, number, position, sensors, redraw).

    Implementace používá:
    - interní framebuffer posunutý o 1 bajt (flush buffer má 145 bajtů),
    - první bajt bufferu je adresa registru PWM (0x24),
    - zbylých 144 bajtů odpovídá fyzickému mapování LED v čipu IS31FL3731.

    Poznámka:
    - Třída je implementována jako singleton – globální instance je dostupná jako `display`.
    """

    rows: int
    """Počet řádků displeje (logicky 7)."""

    cols: int
    """Počet sloupců displeje (logicky 17)."""

    default_brightness: int
    """
    Výchozí jas pro pixely a ikony (0–255).

    Používá se v metodách:
    - `pixel(x, y)` pokud není zadán parametr `color`,
    - `iconA/B/C(icon)` pokud není zadán parametr `color`,
    - `fill()` pokud není zadán parametr `color`.

    Hodnota je interně ořezána do rozsahu 0–255.
    """

    def __init__(self) -> None: ...
    def __new__(cls) -> "Display": ...

    # ---------------------------------------------------------
    # Základní operace s pixely
    # ---------------------------------------------------------

    def pixel(self, x: int, y: int, color: Optional[int] = None) -> None:
        """
        Nastaví jeden pixel na danou hodnotu jasu (0–255).

        Parametry:
        - x: sloupec (0–16), kde 0 je levý okraj displeje a 16 pravý.
        - y: řádek (0–6), kde 0 je horní řádek a 6 spodní.
        - color: jas v rozsahu 0–255. Pokud je `None`, použije se `default_brightness`.

        Chování:
        - Pokud jsou souřadnice mimo rozsah (x < 0, x >= cols, y < 0, y >= rows),
          metoda nic neprovede.
        - Hodnota jasu je oříznuta do rozsahu 0–255.
        - Změna se projeví až po zavolání `flush()` (přímo nebo nepřímo).

        Poznámka:
        - Tato metoda zapisuje přímo do interního flush bufferu (posunutého o 1 bajt),
          takže je velmi rychlá a bez dalších alokací.
        """

    def fill(self, color: Optional[int] = None) -> None:
        """
        Vyplní celý displej jednou hodnotou jasu a ihned provede `flush()`.

        Parametry:
        - color: jas v rozsahu 0–255. Pokud je `None`, použije se `default_brightness`.

        Chování:
        - Nastaví všech 144 fyzických LED na stejnou hodnotu jasu.
        - Hodnota jasu je oříznuta do rozsahu 0–255.
        - Po nastavení všech hodnot se provede `flush()`, takže změna je okamžitě vidět.

        Typické použití:
        - rychlé „vymazání“ displeje (color=0),
        - nastavení jednotného pozadí pro další kreslení.
        """

    def clear(self) -> None:
        """
        Vymaže celý displej (nastaví všechny pixely na 0) a provede `flush()`.

        Chování:
        - Nastaví všech 144 fyzických LED na hodnotu 0 (zhasnuto).
        - Po nastavení všech hodnot se provede `flush()`.
        - Je to ekvivalent `fill(0)`, ale explicitně pojmenovaný pro čitelnost kódu.
        """

    # ---------------------------------------------------------
    # Ikony a ultra-fast bitmapy
    # ---------------------------------------------------------

    def iconA(self, icon: str, flush: bool = True, color: Optional[int] = None) -> None:
        """
        Zobrazí ikonu v pravé části displeje (oblast A).

        Parametry:
        - icon: název ikony (např. '0'–'9', '>', '<', '^', 'v', 'TL', 'TR', 'IT', 'IL', 'IR', 'I+', '-', '_', '.', '|', '/', '\\', 's', 'x', ' ').
        - flush: pokud je True (výchozí), po vykreslení ikony se provede `flush()`.
                 Pokud je False, ikona se pouze připraví v bufferu a je možné
                 vykreslit více ikon najednou a pak zavolat `flush()` ručně.
        - color: jas v rozsahu 0–255. Pokud je `None`, použije se `default_brightness`.

        Chování:
        - Ikona je vykreslena do oblasti A (pravá 5×5 oblast displeje).
        - Využívá ultra-fast bitmapu s předpočítanými indexy do framebufferu.
        - OFF pixely ikony jsou v oblasti A zhasnuty (nastaveny na 0),
          ON pixely jsou nastaveny na daný jas.

        Poznámka:
        - Pro maximální výkon je vhodné volat `iconA(..., flush=False)` pro více ikon
          a následně jednou `flush()`.
        """

    def iconB(self, icon: str, flush: bool = True, color: Optional[int] = None) -> None:
        """
        Zobrazí ikonu ve střední části displeje (oblast B).

        Parametry:
        - icon: název ikony (stejná sada jako u `iconA`).
        - flush: viz `iconA`.
        - color: viz `iconA`.

        Chování:
        - Ikona je vykreslena do oblasti B (střední 5×5 oblast displeje).
        - OFF pixely ikony jsou v oblasti B zhasnuty (0),
          ON pixely jsou nastaveny na daný jas.
        """

    def iconC(self, icon: str, flush: bool = True, color: Optional[int] = None) -> None:
        """
        Zobrazí ikonu v levé části displeje (oblast C).

        Parametry:
        - icon: název ikony (stejná sada jako u `iconA`).
        - flush: viz `iconA`.
        - color: viz `iconA`.

        Chování:
        - Ikona je vykreslena do oblasti C (levá 5×5 oblast displeje).
        - OFF pixely ikony jsou v oblasti C zhasnuty (0),
          ON pixely jsou nastaveny na daný jas.
        """

    # ---------------------------------------------------------
    # Flush a kompatibilní API
    # ---------------------------------------------------------

    def flush(self) -> None:
        """
        Překreslí displej – odešle celý interní framebuffer do LED driveru.

        Chování:
        - Odešle 145 bajtů přes I²C:
          - první bajt je adresa registru PWM (0x24),
          - následuje 144 bajtů jasu pro jednotlivé LED.
        - Používá jediný I²C přenos bez dalších alokací.
        - Čas trvání je dán rychlostí I²C (při 650 kHz cca 3 ms).

        Poznámka:
        - Tato metoda je relativně „drahá“ (v řádu milisekund),
          proto je vhodné ji volat co nejméně často – ideálně jednou
          po sérii změn (např. více ikon s `flush=False`).
        """

    def redraw(self) -> None:
        """
        Alias pro `flush()` – zachovává kompatibilitu s původním API.

        Chování:
        - Jednoduše zavolá `flush()`.
        - Vhodné pro starší kód, který používal `display.redraw()`.
        """

    # ---------------------------------------------------------
    # Senzory a vyšší API
    # ---------------------------------------------------------

    def sensors(
        self,
        obstacleLeft: bool,
        farLeft: Optional[bool],
        left: bool,
        midleLeft: Optional[bool],
        midle35: Optional[bool],
        midleRight: Optional[bool],
        right: bool,
        farRight: Optional[bool],
        obstacleRight: bool,
        bh: int,
        bl: int,
    ) -> None:
        """
        Zobrazí stav senzorů na spodním řádku displeje.

        Parametry:
        - obstacleLeft: True, pokud je překážka vlevo (krajní levý senzor).
        - farLeft: stav vzdálenějšího levého senzoru, nebo None, pokud se nepoužívá.
        - left: stav levého senzoru.
        - midleLeft: stav levého středového senzoru, nebo None.
        - midle35: stav středového senzoru (např. 3.5), nebo None.
        - midleRight: stav pravého středového senzoru, nebo None.
        - right: stav pravého senzoru.
        - farRight: stav vzdálenějšího pravého senzoru, nebo None.
        - obstacleRight: True, pokud je překážka vpravo (krajní pravý senzor).
        - bh: jas aktivního senzoru (0–255).
        - bl: jas neaktivního senzoru (0–255).

        Chování:
        - Na spodním řádku (y=6) rozsvítí jednotlivé pixely podle stavu senzorů.
        - Aktivní senzory mají jas `bh`, neaktivní `bl`.
        - Senzory, které jsou `None`, se ignorují (pixel se nemění).
        - Po nastavení všech pixelů se provede `flush()`.

        Typické použití:
        - vizualizace stavu infra senzorů JoyCaru,
        - ladění logiky sledování čáry nebo překážek.
        """

    def number(self, num: int) -> None:
        """
        Zobrazí tříciferné číslo pomocí ikon A, B a C.

        Parametry:
        - num: celé číslo, které se má zobrazit. Zobrazuje se v rozsahu -99 až 999,
               ale formátování je `{num:3d}`, takže:
               - záporná čísla se zobrazí se znaménkem,
               - kratší čísla jsou zarovnána mezerami zleva.

        Chování:
        - Číslo se převede na řetězec o délce 3 (`"{:3d}".format(num)`).
        - První znak se zobrazí v oblasti A (`iconA`),
        - druhý znak v oblasti B (`iconB`),
        - třetí znak v oblasti C (`iconC`),
        - všechny tři ikony se vykreslí s `flush=False`,
          a na závěr se provede jedno `flush()`.

        Příklady:
        - `number(5)` zobrazí `"  5"` (mezera, mezera, 5),
        - `number(42)` zobrazí `" 42"`,
        - `number(123)` zobrazí `"123"`.
        """

    def drive_mode(self, mode: str, color: Optional[int] = None) -> None:
        """
        Zobrazí režim jízdy v oblasti B (střed displeje).

        Parametry:
        - mode: název ikony, která reprezentuje režim (např. '^', 'v', '>', '<', 'TL', 'TR', 'IT', 'IL', 'IR', 'I+').
        - color: jas v rozsahu 0–255. Pokud je `None`, použije se `default_brightness`.

        Chování:
        - Jednoduše volá `iconB(mode, color=color)`.
        - Slouží jako sémanticky čitelnější alias pro zobrazení směru / režimu jízdy.
        """

    def _position_base(self, a: str, c: str) -> None:
        """
        Interní metoda pro zobrazení pozice pomocí ikon A a C.

        Parametry:
        - a: znak pro oblast A (zobrazí se jako ikona).
        - c: znak pro oblast C (zobrazí se jako ikona).

        Chování:
        - Volá `iconA(a, flush=False)` a `iconC(c, flush=False)`,
          a na závěr provede jedno `flush()`.
        - Tato metoda je základ pro veřejné metody `position()` a `positionEmpty()`.
        """

    def position(self, x: int, y: int) -> None:
        """
        Zobrazí souřadnice (x, y) pomocí ikon A a C.

        Parametry:
        - x: hodnota pro osu X (zobrazí se jako jedna číslice 0–9).
        - y: hodnota pro osu Y (zobrazí se jako jedna číslice 0–9).

        Chování:
        - Hodnoty x a y jsou omezeny na rozsah 0–9 (větší hodnoty se oříznou).
        - `x` se zobrazí v oblasti A (`iconA`),
        - `y` se zobrazí v oblasti C (`iconC`),
        - obě ikony se vykreslí s `flush=False`,
          a na závěr se provede jedno `flush()`.

        Typické použití:
        - zobrazení pozice robota na mřížce,
        - ladění algoritmů pohybu (např. souřadnice v mapě).
        """

    def positionEmpty(self) -> None:
        """
        Vymaže zobrazení pozice (ikony A a C nastaví na mezeru).

        Chování:
        - V oblasti A se zobrazí mezera (`iconA(" ", flush=False)`),
        - v oblasti C se zobrazí mezera (`iconC(" ", flush=False)`),
        - na závěr se provede `flush()`.

        Typické použití:
        - skrytí souřadnic, když nejsou relevantní,
        - návrat do „čistého“ stavu UI.
        """


# Globální instance displeje (singleton)
display: Display
"""
Globální instance třídy `Display`.

Použití:
- `display.pixel(3, 2, 128)`
- `display.iconA("5")`
- `display.number(123)`
- `display.sensors(...)`

Tato instance je vytvořena při importu modulu `Display.py` a sdílí
interní I²C spojení i framebuffer.
"""
