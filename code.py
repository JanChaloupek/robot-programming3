"""
code.py – CuteBotPro line follower s okamžitým zastavením pod stínítkem.

Tato verze:
- NEPOUŽÍVÁ log.flush() nikde mimo hlavní smyčku
- všechny události nastavují need_flush = True
- flush probíhá JEN v hlavní smyčce (status_period nebo need_flush)
- okamžitý STOP při poklesu světla
- reverz pro snížení dojezdu
- blikání spodních LED přes Period (neblokující)
- obnovení jízdy až po stabilním rozjasnění (hysteréza + debounce)
"""

import time
import board
import analogio
import neopixel

from cutebot_pro import CuteBotPro
from utils import Timer, Period, log, LogLevelEnum

# -----------------------------
# Nastavení logování
# -----------------------------
log._level = LogLevelEnum.DEBUG   # chceme vidět vše

# -----------------------------
# Inicializace hardware
# -----------------------------
bot = CuteBotPro()
ldr = analogio.AnalogIn(board.P2)
under = neopixel.NeoPixel(board.P15, 2, brightness=1.0, auto_write=True)

# -----------------------------
# Konfigurace
# -----------------------------
LIGHT_THRESHOLD = 15000
RESUME_HYSTERESIS = 2000
RESUME_DEBOUNCE_MS = 300

BRAKE_REVERSE_SPEED = -40
BRAKE_REVERSE_MS = 150

LINE_PERIOD_MS = 40
BLINK_INTERVAL_S = 0.3
STATUS_PERIOD_MS = 1000

ORANGE = (255, 80, 0)

# -----------------------------
# Timery a periody
# -----------------------------
line_period = Period(timeout_ms=LINE_PERIOD_MS)
blink_period = Period(timeout_ms=int(BLINK_INTERVAL_S * 1000))
status_period = Period(timeout_ms=STATUS_PERIOD_MS)

brake_timer = Timer(timeout_ms=None, startTimer=False)
resume_timer = Timer(timeout_ms=None, startTimer=False)

# -----------------------------
# Stavové proměnné
# -----------------------------
stopped_under_shade = False
blink_state = False
need_flush = False   # <--- CENTRALIZOVANÝ MECHANISMUS

# -----------------------------
# Pomocné funkce
# -----------------------------
def read_light():
    return ldr.value

def hazard_off():
    under.fill((0, 0, 0))

def toggle_blink():
    global blink_state
    blink_state = not blink_state
    color = ORANGE if blink_state else (0, 0, 0)
    under[0] = color
    under[1] = color

def set_motors(left, right):
    """Nastaví motory a zapíše do logu (bez flush)."""
    global need_flush
    left_i = int(left); right_i = int(right)
    log.info(f"Motors -> L:{left_i} R:{right_i}")
    need_flush = True

    try:
        bot.motor_control(2, left_i, right_i)
    except Exception:
        try:
            bot.set_motors(left_i, right_i)
        except Exception:
            print("SET MOTORS", left_i, right_i)

def immediate_stop_and_brake(light_val):
    """Okamžitý reverz + zapnutí blinků."""
    global need_flush
    log.info(f"Shade detected (LDR={light_val}) -> immediate brake")
    need_flush = True

    # reverz
    try:
        bot.motor_control(2, BRAKE_REVERSE_SPEED, BRAKE_REVERSE_SPEED)
    except Exception:
        try:
            bot.set_motors(BRAKE_REVERSE_SPEED, BRAKE_REVERSE_SPEED)
        except Exception:
            pass

    brake_timer.startTimer(timeout_ms=BRAKE_REVERSE_MS)

    # okamžitě rozsvítit blinkry
    under.fill(ORANGE)
    blink_period.startTimer()

def finalize_brake():
    """Po reverzu pevné zastavení."""
    global need_flush
    try:
        bot.motor_control(2, 0, 0)
    except Exception:
        try:
            bot.set_motors(0, 0)
        except Exception:
            pass

    log.info("Brake finished -> hard stop")
    need_flush = True
    brake_timer.stopTimer()

# -----------------------------
# Start
# -----------------------------
log.info("Line follower start (s ochranou proti stínu)")
need_flush = True

# -----------------------------
# Hlavní smyčka
# -----------------------------
while True:
    light = read_light()

    # -----------------------------
    # 1) Okamžitý STOP při poklesu světla
    # -----------------------------
    if light < LIGHT_THRESHOLD:

        if not stopped_under_shade:
            immediate_stop_and_brake(light)
            stopped_under_shade = True
            if resume_timer.isStarted():
                resume_timer.stopTimer()
        else:
            if blink_period.ready():
                toggle_blink()

        if brake_timer.isStarted() and brake_timer.ready():
            finalize_brake()

        # flush v hlavní smyčce
        if status_period.ready() or need_flush:
            log.info(f"STATUS (under shade) LDR={light}")
            log.flush(10)
            need_flush = False

        time.sleep(0.02)
        continue

    # -----------------------------
    # 2) Obnovení jízdy po rozjasnění
    # -----------------------------
    if stopped_under_shade:

        if light >= LIGHT_THRESHOLD + RESUME_HYSTERESIS:
            if not resume_timer.isStarted():
                resume_timer.startTimer(timeout_ms=RESUME_DEBOUNCE_MS)
            else:
                if resume_timer.ready():
                    stopped_under_shade = False
                    resume_timer.stopTimer()
                    blink_period.stopTimer()
                    hazard_off()

                    log.info(f"Ambient restored (LDR={light}) -> resume driving")
                    need_flush = True
        else:
            if resume_timer.isStarted():
                resume_timer.stopTimer()

        if blink_period.ready():
            toggle_blink()

        if status_period.ready() or need_flush:
            log.info(f"STATUS (waiting resume) LDR={light}")
            log.flush(10)
            need_flush = False

        time.sleep(0.02)
        continue

    # -----------------------------
    # 3) Světlo OK → sledování čáry
    # -----------------------------
    hazard_off()
    if blink_period.isStarted():
        blink_period.stopTimer()
        blink_state = False

    if line_period.ready():
        bot.trackbit_state_value()
        state = bot._four_way_state_value

        if state == 0b0110:
            set_motors(40, 40)
        elif state in (0b1100, 0b1000):
            set_motors(20, 40)
        elif state in (0b0011, 0b0001):
            set_motors(40, 20)
        else:
            set_motors(0, 0)

    # -----------------------------
    # 4) CENTRALIZOVANÝ FLUSH
    # -----------------------------
    if status_period.ready() or need_flush:
        last_state = getattr(bot, "_four_way_state_value", None)
        log.info(f"STATUS LDR={light} stopped={stopped_under_shade} state={last_state}")
        log.flush(10)
        need_flush = False

    time.sleep(0.02)
