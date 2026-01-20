# 📘 Superloop — Řešení

Toto je řešení všech úkolů ze studentského worksheetu „Superloop“.  
Kód je psaný tak, aby byl čitelný, jednoduchý a vhodný pro výuku.

---

# 🧪 10) Cvičení — Řešení

## ✔ Úkol 1  
**Napiš komponentu `Blinker`, která bliká LED každých X sekund pomocí Timeru.**

Tato verze bliká **prvním NeoPixelem** na daném pinu.  
Používá objekt `Timer`, takže neblokuje superloop.

```python
from neopixel import NeoPixel

class Blinker:
    def __init__(self, pin, interval, count=8):
        # vytvoříme NeoPixel pásek o daném počtu LED
        self.pixels = NeoPixel(pin, count, auto_write=True)

        # stav LED (svítí / nesvítí)
        self.on = False

        # časovač pro neblokující blikání
        self.timer = Timer(interval)

    def _toggle(self):
        self.on = not self.on
        if self.on:
            self.pixels[0] = (100, 35, 0)   # oranžová
        else:
            self.pixels[0] = (0, 0, 0)     # vypnuto

    def update(self):
        if self.timer.expired():
            self._toggle()
            self.timer.reset()
```

---

## ✔ Úkol 2  
**Napiš komponentu `SensorReader`, která čte senzory každých 0.05 s pomocí Timeru.**

```python
class SensorReader:
    def __init__(self, i2c, interval=0.05, address=0x38):
        self.i2c = i2c
        self.address = address
        self.timer = Timer(interval)
        self.value = None   # poslední přečtená hodnota

    def _read_once(self):
        """Pokusí se přečíst jeden bajt ze senzoru."""
        buffer = bytearray(1)

        if not self.i2c.try_lock():
            return False

        try:
            self.i2c.readfrom_into(self.address, buffer)
            self.value = buffer[0]
            return True
        finally:
            self.i2c.unlock()

    def update(self):
        """Čte senzor jen tehdy, když vypršel interval."""
        if self.timer.expired():
            self._read_once()
            self.timer.reset()
```

---

## ✔ Úkol 3  
**Napiš komponentu `MotorController`, která aktualizuje motory každých 0.02 s pomocí Timeru.**

```python
class MotorController:
    def __init__(self, interval=0.02):
        # Každý motor má vlastní instanci
        self.left_motor = Motor(DirectionEnum.LEFT)
        self.right_motor = Motor(DirectionEnum.RIGHT)

        # Timer řídí frekvenci aktualizace PWM
        self.timer = Timer(interval)

    def _apply_pwm(self):
        """Aplikuje PWM na oba motory bezpečným způsobem."""
        self.left_motor.applyPwmSafely()
        self.right_motor.applyPwmSafely()

    def update(self):
        """Spouští aktualizaci motorů jen tehdy, když vypršel interval."""
        if self.timer.expired():
            self._apply_pwm()
            self.timer.reset()
```

---

## ✔ Úkol 4  
**Přidej všechny komponenty do `Robot.update()`.**

> Poznámka:  
> V původní verzi byly chyby — komponenty dostávaly špatné argumenty.  
> Tady je **opravená a funkční verze**.

```python
class Robot:
    def __init__(self, i2c, neopixel_pin):
        # komponenty
        self.heartbeat = HeartbeatLED(neopixel_pin, 0.25)
        self.blinker = Blinker(neopixel_pin, 0.5)
        self.sensors = SensorReader(i2c)
        self.motors = MotorController()

    def update(self):
        self.heartbeat.update()
        self.blinker.update()
        self.sensors.update()
        self.motors.update()
```

---

## ✔ Úkol 5  
**Zkus do superloopu dát `time.sleep(1)` a pozoruj, co se stane.**

### Očekávané chování:
- robot přestane reagovat  
- senzory se nečtou  
- motory se neaktualizují  
- LED přestane blikat  

### Proč:
`time.sleep()` **zastaví celý superloop**, takže žádná komponenta nedostane šanci běžet.

---

# 🚀 11) Úkoly pro pokročilé — Řešení

## ✔ Úkol A — Komponenta, která volá jiné komponenty  
**LineFollower**

```python
class LineFollower:
    def __init__(self, sensors, motors):
        self.sensors = sensors
        self.motors = motors

    def update(self):
        if self.sensors.leftActive():
            self.motors.turnLeft()
        elif self.sensors.rightActive():
            self.motors.turnRight()
        else:
            self.motors.forward()
```

---

## ✔ Úkol B — Stavový automat

```python
class RobotState:
    IDLE = 0
    FOLLOW_LINE = 1
    AVOID_OBSTACLE = 2

class StateMachine:
    def __init__(self, sensors, motors):
        self.state = RobotState.IDLE
        self.sensors = sensors
        self.motors = motors

    def update(self):
        if self.state == RobotState.IDLE:
            self.motors.stop()
            if self.sensors.seesLine():
                self.state = RobotState.FOLLOW_LINE

        elif self.state == RobotState.FOLLOW_LINE:
            if self.sensors.obstacleAhead():
                self.state = RobotState.AVOID_OBSTACLE
            else:
                self.motors.forward()

        elif self.state == RobotState.AVOID_OBSTACLE:
            self.motors.turnRight()
            if not self.sensors.obstacleAhead():
                self.state = RobotState.FOLLOW_LINE
```

---

## ✔ Úkol C — Watchdog

```python
class Watchdog:
    def __init__(self, timeout=1.0):
        self.timer = Timer(timeout)

    def kick(self):
        self.timer.reset()

    def update(self):
        if self.timer.expired():
            print("EMERGENCY STOP")
```

---

## ✔ Úkol D — Měření FPS superloopu

```python
class FPSCounter:
    def __init__(self):
        self.frames = 0
        self.timer = Timer(1.0)

    def update(self):
        self.frames += 1
        if self.timer.expired():
            print("FPS:", self.frames)
            self.frames = 0
            self.timer.reset()
```

---

# 🏁 Shrnutí

Tahle řešení ukazují:

- jak psát čisté komponenty  
- jak používat Timer  
- jak stavět vlastní plánovače  
- jak dělat animace, stavové automaty a watchdogy  
- jak superloop drží celý robot pohromadě  
