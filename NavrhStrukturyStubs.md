# 📁 Návrh ideální struktury `_stubs/`

Tady máš kompletní, čistou a dlouhodobě udržitelnou strukturu `_stubs/`, která:

- je neviditelná pro studenty  
- je jasná pro instruktory  
- podporuje fake hardware, stub moduly i deterministické testování  
- je modulární a snadno rozšiřitelná  
- odpovídá tomu, jak už máš postavený test runner  

---

## 📁 Doporučená struktura

```
_stubs/
│
├─ __init__.py
│
├─ time.py                # deterministický čas
├─ adafruit_ticks.py      # deterministické tickování
│
├─ board.py               # fake board piny
├─ busio.py               # fake I2C/SPI/UART
├─ digitalio.py           # fake DigitalInOut
├─ analogio.py            # fake AnalogIn
├─ pwmio.py               # fake PWMOut
├─ neopixel.py            # fake NeoPixel
│
├─ picoed.py              # fake pico:ed API (tlačítka, display, I2C…)
│
├─ hardware/              # (volitelné) detailní fake implementace
│   ├─ __init__.py
│   ├─ fake_i2c_device.py
│   ├─ fake_motor.py
│   ├─ fake_neopixel_hw.py
│   └─ ...
│
├─ utils/                 # pomocné nástroje pro testy
│   ├─ __init__.py
│   ├─ deterministic_random.py
│   ├─ fake_logger.py
│   └─ ...
│
└─ typing/                # stuby pro typové kontroly (volitelné)
    ├─ __init__.py
    ├─ neopixel.pyi
    ├─ busio.pyi
    └─ ...
```

---

## 🧠 Proč je tahle struktura ideální

### 1) `_stubs/` je interní a studenti ho ignorují  
Podtržítko je geniální trik — studenti to automaticky přeskočí.

### 2) Fake moduly mají stejná jména jako skutečné CircuitPython moduly  
To je klíčové pro test runner i import přesměrování.

### 3) `hardware/` umožňuje oddělit „nižší vrstvu“  
Simulace motorů, I2C zařízení, NeoPixel bufferů atd.

### 4) `utils/` je místo pro věci, které nejsou hardware  
Deterministický random, fake logger, helpery.

### 5) `typing/` je volitelné, ale velmi užitečné  
Pro lepší IntelliSense a typové kontroly.

---

## 🔧 Jak to zapadá do tvého test runneru

Stačí změnit:

```python
LIB_DIR = os.path.join(BASE_DIR, "_stubs")
```

A:

```python
module = importlib.import_module(f"_stubs.{name}")
```

Nic dalšího.

---

## 🧩 Doporučené rozložení podle odpovědnosti

### 🔹 Vrstva 1 — API kompatibilita  
Soubor = modul CircuitPythonu

- `board.py`
- `busio.py`
- `digitalio.py`
- `analogio.py`
- `pwmio.py`
- `neopixel.py`
- `picoed.py`
- `time.py`
- `adafruit_ticks.py`

### 🔹 Vrstva 2 — Fake hardware (detailní simulace)

- `hardware/fake_motor.py`
- `hardware/fake_neopixel_hw.py`
- `hardware/fake_i2c_device.py`

### 🔹 Vrstva 3 — Pomocné nástroje

- `utils/deterministic_random.py`
- `utils/fake_logger.py`

---

## 🏁 Shrnutí

Tahle struktura `_stubs/` ti dá:

- čistotu  
- modularitu  
- dlouhodobou udržitelnost  
- jasné oddělení API vs. simulace  
- minimální kognitivní zátěž pro studenty  
- maximální sílu pro testy  

A hlavně:  
**zapadá to přesně do tvé filozofie — čisté, učitelné, predikovatelné.**
