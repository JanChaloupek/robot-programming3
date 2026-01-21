# Porovnání tří časovacích funkcí v CircuitPythonu

Toto srovnání shrnuje rozdíly mezi **adafruit_ticks**, **time.monotonic()** a **time.monotonic_ns()** z hlediska přesnosti, vhodnosti pro superloop, práce s přetečením a praktického použití.

---

## 🧭 Přehled

| Funkce | Typ hodnoty | Přesnost | Přetečení | Bezpečné porovnání | Vhodné pro |
|-------|--------------|----------|-----------|---------------------|-------------|
| **adafruit_ticks** (`ticks_ms`) | integer (ms) | stabilní | ~6,2 dne | ano (`ticks_diff`) | superloop, periodické úlohy, debounce, robotika |
| **time.monotonic()** | float (s) | klesá v čase | ne | ne | lidsky čitelné časy, logování |
| **time.monotonic_ns()** | integer (ns) | vysoká | prakticky ne | ne (musíš řešit sám) | profilování, měření krátkých intervalů |

---

## 🧩 Detailní charakteristika

### **1. adafruit_ticks (ticks_ms, ticks_diff, …)**
- Vrací **celé číslo v milisekundách**.
- Přesnost se **nezhoršuje** s dobou běhu.
- Přetečení je **bezpečné** díky `ticks_diff()`.
- Navrženo přímo pro **superloop**, stavové automaty a periodické úlohy.
- Standard v Adafruit knihovnách.

**Výhody:**
- stabilní přesnost,
- bezpečné porovnání,
- ideální pro robotiku a testovací prostředí.

---

### **2. time.monotonic()**
- Vrací **float v sekundách**.
- Po delší době běhu float ztrácí rozlišení → rozdíly mohou být nepřesné.
- Nepřetéká, ale není vhodný pro přesné plánování.

**Výhody:**
- lidsky čitelný čas,
- dobré pro logování nebo měření delších intervalů.

**Nevýhody:**
- ztráta přesnosti po hodinách/dnech,
- nevhodné pro přesné řízení.

---

### **3. time.monotonic_ns()**
- Vrací **64bit integer v nanosekundách**.
- Nepoužívá float → přesnost se nezhoršuje.
- Přetečení je teoreticky možné, ale v praxi nereálné.
- Není navrženo pro plánování, chybí wrap‑safe API.

**Výhody:**
- vysoké rozlišení,
- vhodné pro profilování nebo měření velmi krátkých úseků.

**Nevýhody:**
- žádné pomocné funkce pro plánování,
- různé platformy mohou mít různé skutečné rozlišení.

---

## 🧠 Doporučení pro praxi

- **Pro superloop, robotiku, periodické úlohy → `adafruit_ticks`**  
  Nejbezpečnější a nejstabilnější volba.

- **Pro lidsky čitelné časy → `time.monotonic()`**

- **Pro profilování a měření krátkých intervalů → `time.monotonic_ns()`**

---

## 🧪 Mini‑příklady

### Periodická úloha (správně)
```python
import adafruit_ticks as ticks

next_time = ticks.ticks_add(ticks.ticks_ms(), 100)

while True:
    if ticks.ticks_diff(next_time, ticks.ticks_ms()) <= 0:
        print("tick")
        next_time = ticks.ticks_add(next_time, 100)
```

### Měření krátkého úseku
```python
import time

start = time.monotonic_ns()
# ... kód ...
elapsed_ns = time.monotonic_ns() - start
```

### Lidsky čitelné logování
```python
import time

print("Start:", time.monotonic())
```

