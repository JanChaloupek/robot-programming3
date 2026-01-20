# 📘 Superloop

## 🎯 Cíl
- pochopíš superloop pomocí jednoduchých metafor  
- naučíš se, proč robot nesmí používat `sleep()`  
- zvládneš časování bez blokování  
- uvidíš, jak robot zvládá více úloh najednou  
- naučíš se objektový styl s metodou `update()`  
- pochopíš, jak to souvisí s asyncio  
- naučíš se používat objekt `Timer`  

---

# 🍳 1) Úvodní metafora: kuchař v restauraci

Představ si kuchaře:

- míchá polévku  
- kontroluje maso  
- otáčí brambory  
- sleduje troubu  

Nemá čtyři mozky.  
Jen **rychle přepíná** mezi úkoly.

👉 Přesně tak funguje superloop v robotovi.

Robot nedělá věci paralelně.  
Jen rychle střídá malé kousky práce.

---

# 🎻 2) Metafora: robot jako orchestr

Robot je jako orchestr:

- dirigent = superloop  
- hudebníci = komponenty (motory, senzory, LED, displej)  
- každý hudebník ví, kdy má hrát  
- dirigent jen říká: „hrajem dál“  

👉 To je `robot.update()`.

---

# 🛑 3) Klíčová myšlenka: **Nikdy nic neblokuj**

Zkus:

```python
while True:
    print("A")
    time.sleep(1)
    print("B")
```

Robot:

- nereaguje  
- nečte senzory  
- neřídí motory  

`time.sleep()` zastaví celý robot.

👉 **Superloop funguje jen tehdy, když každá část běží rychle a nic nečeká.**

---

# ⏱️ 4) Jak dělat časování správně

Používá se `time.monotonic()`:

```python
import time

last = time.monotonic()

while True:
    now = time.monotonic()

    if now - last > 0.5:
        print("blik")
        last = now
```

Robot mezitím může dělat další věci.

---

# 🔁 5) Více úloh najednou

Úkol:  
Blikej LED každých 0.5 s a tiskni „tick“ každých 0.2 s.

```python
import time

last_led = time.monotonic()
last_tick = time.monotonic()

while True:
    now = time.monotonic()

    if now - last_led > 0.5:
        print("LED")
        last_led = now

    if now - last_tick > 0.2:
        print("tick")
        last_tick = now
```

Robot zvládá obě úlohy současně, protože nic neblokuje.

---

# 🧩 6) Objekt Timer

`Timer` je malý objekt, který si pamatuje čas posledního spuštění a umí říct, jestli už vypršel interval.  
Používá se místo `sleep()`, protože **neblokuje** robota.

## Implementace

```python
import time

class Timer:
    def __init__(self, interval):
        self.interval = interval
        self.last = time.monotonic()

    def expired(self):
        return time.monotonic() - self.last >= self.interval

    def reset(self):
        self.last = time.monotonic()
```

---

# 🔌 7) Použití Timeru v komponentě

```python
class HeartbeatLED:
    def __init__(self, led, interval):
        self.led = led
        self.timer = Timer(interval)

    def update(self):
        if self.timer.expired():
            self.led.toggle()
            self.timer.reset()
```

---

# 🚗 8) Objektový superloop

### Robot skládá komponenty:

```python
class Robot:
    def __init__(self):
        from picoed import led
        self.heartbeat = HeartbeatLED(led, 0.25)

    def update(self):
        self.heartbeat.update()
```

### Superloop:

```python
robot = Robot()

while True:
    robot.update()
```

---

# 🔌 9) Přirovnání k asyncio

Pokud znáš asyncio, superloop je vlastně totéž:

### Asyncio:
```python
await asyncio.sleep(0.25)
```

### Superloop:
```python
if timer.expired():
    timer.reset()
```

V asyncio úloha „pustí řízení“ pomocí `await`.  
V superloopu úloha „pustí řízení“ tím, že rychle skončí a vrátí se do smyčky.

👉 **Superloop = ručně napsané asyncio, které funguje i na robotovi.**

---

# 🧪 10) Cvičení

### Úkol 1  
Napiš komponentu `Blinker`, která bliká LED každých X sekund pomocí Timeru.

### Úkol 2  
Napiš komponentu `SensorReader`, která čte senzory každých 0.05 s pomocí Timeru.

### Úkol 3  
Napiš komponentu `MotorController`, která aktualizuje motory každých 0.02 s pomocí Timeru.

### Úkol 4  
Přidej všechny komponenty do `Robot.update()`.

### Úkol 5  
Zkus do superloopu dát `time.sleep(1)` a pozoruj, co se stane.

---

# 🚀 11) Úkoly pro pokročilé

### Úkol A — Komponenta, která volá jiné komponenty  
`LineFollower(sensors, motors)`.

### Úkol B — Stavový automat  
Stavy: `IDLE`, `FOLLOW_LINE`, `AVOID_OBSTACLE`.

### Úkol C — Watchdog  
Pokud se 1 s nevolá `kick()`, vypiš „EMERGENCY STOP“.

### Úkol D — Měření FPS superloopu  
Kolikrát za sekundu proběhne smyčka.

---

# 🏁 12) Co si máš odnést

- Superloop je základ robotiky  
- Robot rychle přepíná mezi úlohami  
- `sleep()` je zakázaný — blokuje celý robot  
- Časování se dělá přes `Timer` nebo `monotonic()`  
- Objektový styl s `update()` je nejpřehlednější  
- Superloop je jako asyncio, jen bez `await`  
