"""
code.py – Hlavní výukový řídicí program robota JoyCar s Pico:ed.

===============================================================================
VZOROVÝ VÝUKOVÝ PROJEKT PRO STUDENTY
Předmět: Základy stavby a programování robotů
Platforma: Elecfreaks JoyCar s deskou Pico:ed v2 (CircuitPython)
===============================================================================

Architektura programu (Model Superloop):
----------------------------------------
Tento program je postaven podle vzoru „Superloop s kooperativním multitaskingem“.
V robotice NESMÍME používat blokující čekání typu `time.sleep()`.

Představte si robota jako orchestr:
- `JoyCarRobot` (robot) sdružuje jednotlivé hudebníky (motory, senzory, světla, bzučák, displej).
- `CPU` (plánovač) a stavové automaty jsou dirigent, který udává takt a rozhoduje o strategii.
- Hlavní smyčka `while True:` představuje neustálý běh času. V každém taktu:
    1. `CPU.tick()`   -> zkontroluje stav a vyhodnotí další krok mise (např. odbočit vlevo).
    2. `robot.update()` -> přečte senzory, nastaví PWM na motory, aktualizuje blinkry a tóny bzučáku.

Podrobné výukové materiály pro studenty:
----------------------------------------
- Proč nepoužívat sleep: file:///C:/Projekty/pomucky/superloop.md
- Přesné časování tiku:  file:///C:/Projekty/pomucky/compare_tick_function.md
- Blokování v Pythonu:   file:///C:/Projekty/pomucky/sleep.md

Jak program funguje:
--------------------
1. Inicializuje hardware robota (`createJoyCarRobot()`).
2. Zkontroluje a zobrazí napětí baterie na maticovém displeji Pico:ed.
3. Zahraje uvítací melodii `hello` zcela na pozadí (neblokující HornController).
4. Sestaví navigační trasu křižovatek (objekt `Commands`) a spustí stavový automat `CrossRoadsSM`.
5. Běží v neblokující smyčce, dokud student nestiskne tlačítko A (`button_a`).
6. Při stisku tlačítka A robot bezpečně zastaví.
7. V případě neočekávané výjimky bezpečně vypne všechny motory a subsystémy (`emergencyShutdown()`).

Úkoly a experimenty pro studenty:
---------------------------------
1. Změňte plán trasy v proměnné `route`:
   Vyzkoušejte např. projet trasu se střídavým odbočováním:
   `route = Commands([DirectionEnum.LEFT, DirectionEnum.RIGHT, DirectionEnum.FORWARD])`
2. Zkuste jednoduché sledování čáry bez křižovatek:
   Zakomentujte `CPU.add(...)` a do smyčky vložte:
   `robot.rideLine(baseSpeed=0.2, turnGain=0.4)`
"""

import time
import board
from picoed import button_a, i2c as pico_i2c

from joycar import (
    createJoyCarRobot,
    DirectionEnum,
    Commands,
    CrossRoadsSM,
    CPU,
    Display,
    display,
    hello,
    tutu,
    panic,
    log,
    LogLevelEnum,
)
from joycar.battery import battery_voltage
from utils.period import Period


def main():
    """Hlavní vstupní funkce robota JoyCar."""
    robot = None

    try:
        log.info("=== JoyCar Robot Start ===")

        # Periodický časovač pro neblokující výpis logů
        log_flush_period = Period(timeout_ms=500)

        # ---------------------------------------------------------------------
        # 1. Diagnostika baterie a displeje
        # ---------------------------------------------------------------------
        voltage = battery_voltage()
        if voltage is not None:
            log.info(f"Napětí baterie: {voltage:.2f} V")
            # Zobrazíme napětí vynásobené 10 (např. 4.8 V se zobrazí jako 48)
            display.number(int(voltage * 10))
            time.sleep(1.0)
        else:
            log.info("Napětí baterie nelze změřit (běh na USB nebo simulátor)")
            display.drive_mode('s')
            time.sleep(0.5)

        # ---------------------------------------------------------------------
        # 2. Inicializace robota
        # ---------------------------------------------------------------------
        # createJoyCarRobot() vytvoří robota se všemi subsystémy:
        # - robot.wheels   : řízení dvou DC motorů přes PCA9633
        # - robot.sensors  : čtení 3 IR senzorů čáry a 2 překážkových přes PCF8574
        # - robot.lights   : 8 NeoPixel LED (potkávací světla, blinkry, brzdová)
        # - robot.horn     : neblokující bzučák
        robot = createJoyCarRobot()

        # Zvukové uvítání studenta
        robot.playHonk(hello)

        # ---------------------------------------------------------------------
        # 3. Nastavení navigačního plánu trasy
        # ---------------------------------------------------------------------
        # Zde student zadává sekvenci odbočení na křižovatkách:
        # DirectionEnum.LEFT     = odbočit vlevo
        # DirectionEnum.RIGHT    = odbočit vpravo
        # DirectionEnum.FORWARD  = pokračovat rovně
        #
        # Příklad: čtvercový okruh se 4 odbočeními vlevo:
        route = Commands([
            DirectionEnum.LEFT,
            DirectionEnum.LEFT,
            DirectionEnum.LEFT,
            DirectionEnum.LEFT,
        ])

        # Vytvoření stavového automatu pro autonomní navigaci křižovatkami
        sm = CrossRoadsSM(robot, commands=route)
        CPU.clear()
        CPU.add(sm)

        log.info("Robot připraven. Spouštím Superloop smyčku (pro zastavení stiskněte tlačítko A)...")
        log.flush()

        # ---------------------------------------------------------------------
        # 4. Hlavní Superloop smyčka
        # ---------------------------------------------------------------------
        while not button_a.was_pressed():
            # 1. Krok rozhodovací logiky stavového automatu
            CPU.tick()

            # 2. Krok hardwarových periferií (senzory, motory, světla, zvuk, displej)
            robot.update()

            # 3. Dávkový výpis zpráv z paměťového bufferu (udržuje superloop plynulý)
            if log_flush_period.ready():
                log.flush(max_line=5)

            # Pokud stavový automat dokončil celou trasu, ukončíme jízdu
            if not CPU.existSM():
                log.info("Trasa byla úspěšně dokončena!")
                break

        # ---------------------------------------------------------------------
        # 5. Bezpečné zastavení po dojezdu nebo stisku tlačítka A
        # ---------------------------------------------------------------------
        log.info("Zastavuji robota...")
        robot.stop()
        display.drive_mode('s')
        robot.playHonk(tutu)
        log.flush()

    except Exception as e:
        # Bezpečnostní pojistka: při jakékoliv chybě okamžitě nouzově vypneme vše
        log.error(f"POZOR: Došlo k chybě: {e}")
        log.flush()
        if robot is not None:
            robot.emergencyShutdown()
        display.drive_mode('x')
        raise e


if __name__ == "__main__":
    main()
