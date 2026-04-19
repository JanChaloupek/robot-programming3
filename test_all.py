"""
test_all.py — Kompletní testovací skript pro Cutebot Pro V2 (Pico:ed + CircuitPython)

Tento soubor NEspouští Pico:ed automaticky.
Musí být spuštěn z code.py, například takto:

    from cutebot_pro import CuteBotPro
    from test_all import run_all_tests

    bot = CuteBotPro()
    run_all_tests(bot)

DŮLEŽITÉ:
- Funkce run_all_tests(bot) provede kompletní diagnostiku Cutebot Pro V2.
- Testuje všechny příkazy protokolu 0x10–0x86.
- Testy jsou bezpečné, ale robot se bude pohybovat — dej ho na volnou plochu.
- Každý test má krátkou pauzu, aby bylo vidět, co robot dělá.

OBSAH TESTŮ:
1) Čtení verze firmware
2) Světla (RGB)
3) Přímé řízení motorů (bez PID)
4) Čtení rychlosti a vzdálenosti
5) PID rychlost (0x80)
6) PID vzdálenost (0x81)
7) PID vzdálenost + rychlost (0x84)
8) PID úhel (0x83)
9) PID úhel + rychlost (0x86)
10) PID steering (0x82)
11) PID steering + rychlost (0x85)
12) Line follower (0x60)
13) Servo (0x40)
14) Rozšiřující motor (0x30)
15) Block mode

Pokud chceš testovat jen některé části,
můžeš je jednoduše zakomentovat nebo vytvořit vlastní testovací funkce.
"""

from time import sleep
from cutebot_pro import CuteBotPro 

def run_all_tests(bot: CuteBotPro) -> None:
    """
    Spustí kompletní testovací sekvenci Cutebot Pro V2.

    Parametr:
        bot — instance CuteBotPro()

    """
    print("Spouštím kompletní test Cutebot Pro V2...")

    # ----------------------------------------------------------------------
    print("=== TEST 1: Čtení verze firmware ===")
    print("Firmware:", bot.read_versions())
    sleep(1)

    # ----------------------------------------------------------------------
    print("\n=== TEST 2: Světla ===")
    print("Zapínám levé světlo na červenou")
    bot.color_light(0, 0xFF0000)
    sleep(1)

    print("Zapínám pravé světlo na zelenou")
    bot.color_light(1, 0x00FF00)
    sleep(1)

    print("Zapínám obě světla na modrou")
    bot.color_light(2, 0x0000FF)
    sleep(1)

    print("Vypínám světla")
    bot.turn_off_all_headlights()
    sleep(1)

    # ----------------------------------------------------------------------
    print("\n=== TEST 3: Přímé řízení motorů (bez PID) ===")
    print("Jedu dopředu pomalu")
    bot.motor_control(2, 30, 30)
    sleep(1)

    print("Jedu dozadu pomalu")
    bot.motor_control(2, -30, -30)
    sleep(1)

    print("Zatáčím doleva")
    bot.motor_control(2, -30, 30)
    sleep(1)

    print("Zatáčím doprava")
    bot.motor_control(2, 30, -30)
    sleep(1)

    print("STOP")
    bot.motor_control(2, 0, 0)
    sleep(1)

    # ----------------------------------------------------------------------
    print("\n=== TEST 4: Čtení rychlosti a vzdálenosti ===")
    print("Rychlost levého kola:", bot.read_speed(0))
    print("Rychlost pravého kola:", bot.read_speed(1))
    print("Vzdálenost levého kola:", bot.read_distance(0))
    print("Vzdálenost pravého kola:", bot.read_distance(1))
    sleep(1)

    # ----------------------------------------------------------------------
    print("\n=== TEST 5: PID rychlost (0x80) ===")
    print("PID: jedu vpřed 20 cm/s")
    bot.pid_speed_control(20, 20, 0)
    sleep(2)

    print("PID: STOP")
    bot.pid_speed_control(0, 0, 0)
    sleep(1)

    # ----------------------------------------------------------------------
    print("\n=== TEST 6: PID vzdálenost (0x81) ===")
    print("PID: jedu vpřed 10 cm")
    bot.pid_run_distance(0, 10, 0)
    sleep(1)

    # ----------------------------------------------------------------------
    print("\n=== TEST 7: PID vzdálenost + rychlost (0x84) ===")
    print("PID: jedu vpřed 15 cm rychlostí 30 cm/s")
    bot.pid_speed_run_distance(30, 0, 0, 15, 0)
    sleep(1)

    # ----------------------------------------------------------------------
    print("\n=== TEST 8: PID úhel (0x83) ===")
    print("PID: otočím levé kolo o 90°")
    bot.pid_run_angle(0, 90, 0)
    sleep(1)

    # ----------------------------------------------------------------------
    print("\n=== TEST 9: PID úhel + rychlost (0x86) ===")
    print("PID: otočím obě kola o 180° rychlostí 50 %")
    bot.pid_speed_run_angle(50, 2, 180, 0)
    sleep(1)

    # ----------------------------------------------------------------------
    print("\n=== TEST 10: PID steering (0x82) ===")
    print("PID: zatáčím doleva o 45°")
    bot.pid_run_steering(0, 45)
    sleep(1)

    # ----------------------------------------------------------------------
    print("\n=== TEST 11: PID steering + rychlost (0x85) ===")
    print("PID: zatáčím doprava o 45° rychlostí 40 %")
    bot.pid_speed_run_steering(40, 1, 45)
    sleep(1)

    # ----------------------------------------------------------------------
    print("\n=== TEST 12: Line follower (0x60) ===")
    print("Čtu stav 4kanálového senzoru")
    bot.trackbit_state_value()
    print("Stav:", bot._four_way_state_value)

    print("Gray hodnoty:")
    for ch in range(4):
        print(f"  CH{ch} =", bot.trackbit_get_gray(ch))

    print("Offset:", bot.get_offset())
    sleep(1)

    # ----------------------------------------------------------------------
    print("\n=== TEST 13: Servo (0x40) ===")
    print("Servo M1 → 0°")
    bot.extend_servo_control(1, 0, 0)
    sleep(1)

    print("Servo M1 → 90°")
    bot.extend_servo_control(1, 0, 90)
    sleep(1)

    print("Servo M1 → 180°")
    bot.extend_servo_control(1, 0, 180)
    sleep(1)

    # ----------------------------------------------------------------------
    print("\n=== TEST 14: Rozšiřující motor (0x30) ===")
    print("Motor dopředu")
    bot.extend_motor_control(50)
    sleep(1)

    print("Motor dozadu")
    bot.extend_motor_control(-50)
    sleep(1)

    print("Motor STOP")
    bot.extend_motor_stop()
    sleep(1)

    # ----------------------------------------------------------------------
    print("\n=== TEST 15: Block mode ===")
    print("Nastavuji délku bloku na 10 cm")
    bot.pid_block_set(10, 0)

    print("Jedu 2 bloky (20 cm)")
    bot.pid_run_block(2)
    sleep(1)

    # ----------------------------------------------------------------------
    print("\n=== HOTOVO ===")
    bot.motor_control(2, 0, 0)
    bot.turn_off_all_headlights()
    print("Všechny testy dokončeny.")
