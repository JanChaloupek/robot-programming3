# Architektura a dokumentace software JoyCar (`3-SW_GIT`)

Vítejte v dokumentaci řídicího softwaru pro výukového robota **JoyCar** s mikrokontrolérem **Pico:ed v2** (CircuitPython).

Tento adresář obsahuje kompletní architektonický popis systému, návody pro studenty a třídní diagramy v jazyce **PlantUML**.

---

## 1. Doporučení ke struktuře a názvu adresáře

V předchozím ročníku (`2-SW_GIT`) byl dokumentační adresář pojmenován `doc/`.
V moderních open-source projektech a Python standardech (včetně GitHub Pages, ReadTheDocs a MkDocs) je doporučeným názvem **`docs/`** (s 's' na konci):
- `docs/` je standardní konvence, kterou automaticky rozpoznává většina nástrojů a GitHub.
- Diagramy a UML modely jsou přehledně umístěny v podadresáři `docs/diagrams/`.

---

## 2. Přehled architektury (Superloop a Facade)

Software robota je postaven na dvou klíčových návrhových vzorech:
1. **Facade (`JoyCarRobot`):** Sdružuje všechny hardwarové periferie (senzory, motory, světla, zvuk, textový displej) do jednotného rozhraní pro studenty.
2. **Superloop:** Všechny komponenty fungují neblokujícím způsobem (bez `time.sleep()`), řízené periodickou metodou `robot.update()` a plánovačem `CPU.tick()`.

```mermaid
flowchart TD
    Main["code.py (Hlavní smyčka)"] --> Robot["JoyCarRobot (Fasáda)"]
    Main --> CPU["CPU.tick() (Stavový automat)"]

    Robot --> Sensors["Sensors (2–6 optočlenů + překážky)"]
    Robot --> Wheels["Wheels (Diferenciální podvozek)"]
    Robot --> Lights["LightsControl (NeoPixel páska)"]
    Robot --> Horn["HornController (Zvuk / melodie)"]
    Robot --> LCD["TextDisplay (Alfanumerické LCD)"]
    Robot --> Sonar["Sonar (Ultrazvuk HC-SR04 v metrech)"]

    Wheels --> WheelLeft["Wheel (Levé kolo)"]
    Wheels --> WheelRight["Wheel (Pravé kolo)"]
    WheelLeft --> Driver["Budič PWM (PCA9633 / PCA9685)"]
    WheelRight --> Driver
    WheelLeft o-- Calib["CalibrateFactors (Lineární model)"]
    WheelRight o-- Calib
```

---

## 3. Podpora různého hardwaru a snadné přepínání

### A) Budiče motorů (PCA9633 vs. PCA9685)
- **8bitový PCA9633:** Výchozí čip na základní desce JoyCaru (rozsah PWM `-255 .. +255`).
- **12bitový PCA9685:** Rozšiřující / náhradní deska při spálení původního H-můstku (rozsah PWM `-4095 .. +4095`).
- **Přepnutí jedním parametrem:**
  ```python
  robot = createJoyCarRobot(driver="PCA9685")
  ```

### B) Kalibrační model motorů (`CalibrateFactors`)
Každé stejnosměrné stejnosměrné kolo má drobnou odchylku a minimální rozjezdové napětí (deadzone). Model převádí úhlovou rychlost $\omega$ v rad/s na PWM:
$$PWM = a \cdot |\omega| + b$$
Přednastavené tovární profily:
```python
cal_8bit = CalibrateFactors.forPCA9633(a=17.0, b=28.0)
cal_12bit = CalibrateFactors.forPCA9685(a=272.0, b=448.0)
```

### C) Sledování čáry (2 až 6 senzorů)
Strategie vyhodnocování čáry je oddělena do přehledných tříd (`LineTracker2` .. `LineTracker6`):
- `LineTracker2`: 2 senzory (levý/pravý) pro začátečníky.
- `LineTracker3`: 3 tovární senzory (výchozí).
- `LineTracker4`: 4 senzory (2 středové + 2 vnější).
- `LineTracker5`: 5 senzorů (3 středové + 2 předsazené krajní).
- `LineTracker6`: 6 senzorů (plná výbava z 2-SW_GIT s 9 zónami odchylky).
- **Nastavení při inicializaci nebo za běhu:**
  ```python
  robot = createJoyCarRobot(line_sensors=5)
  # nebo za běhu:
  robot.sensors.setLineSensorCount(4)
  ```

### D) Alfanumerický textový displej (`TextDisplay`)
- Připojen přes I2C expandér PCF8574 (adresa `0x27` nebo `0x3F`).
- **Vypínatelný za běhu (`enable()` / `disable()`):** Pokud není displej připojen nebo je vypnutý, vůbec nezatěžuje I2C sběrnici a robot funguje dál bez jakýchkoli chyb.
- Speciální metoda pro výuku odometrie: `writePosition(x, y, theta)`.

### E) Ultrazvukový senzor překážek (`Sonar`) v základních jednotkách SI
- **Hardwarové zapojení:** Piny `board.P8` (Trigger) a `board.P12` (Echo).
- **Striktní dodržování základních jednotek SI:** Všechny vzdálenosti jsou výhradně v **metrech [m]** (např. bezpečný odstup `0.20 m`, nikoliv centimetry).
- **Neblokující řízení v Superloop:** Využívá časovač `Period(timeout_ms=60)` pro měření bez brzdění hlavní smyčky.
- **Vyhlazovací filtr:** Klouzavý průměr ze 3 vzorků eliminuje falešné odrazy a zákmity.
- **Vypínatelný za běhu (`enable()` / `disable()`):** Pokud robot sonar fyzicky nemá, zůstává neaktivní.
- **Integrace s řízením robota:**
  ```python
  robot = createJoyCarRobot(sonar_enabled=True)
  # Rychlý dotaz na překážku do 0.20 m:
  if robot.isObstacleAhead(distance_m=0.20):
      robot.stop()
  # Nebo automatické zastavení v autonomní jízdě:
  robot.rideLine(baseSpeed=0.25, minObstacleDistance=0.20)
  ```

### F) LEDka života (Heartbeat LED)
- **Vizuální indikátor běhu:** Deska Pico:ed obsahuje stavovou LED (`picoed.led`). V metodě `robot.update()` probíhá neblokující přepínání této LED v periodě 150 ms pomocí `Period(timeout_ms=150)`.
- **Diagnostika pro studenty i pedagogy:** Dokud robot běží a hlavní smyčka Superloop nezamrzla (např. v nechtěném `time.sleep()` nebo nekonečném cyklu), LED rovnoměrně pulzuje. Při neočekávané chybě, zastavení nebo `robot.emergencyShutdown()` se LED automaticky zhasne.

### G) Stavový automat (SM) a kooperativní plánovač CPU (`utils/sm.py`)
- **Umístění modulu:**
  - Stavový automat a plánovač CPU jsou zcela nezávislé na hardwaru robota a jsou umístěny v balíčku `utils/sm.py` (dostupné přímo přes `from utils import CPU, AbstractSM, Task, Step`).
- **Autorství a původ architektury:**
  - Původní architekturu a jádro stavového automatu (třídy `CPU`, `Task`, `AbstractSM`) vytvořil student **Martin Dostál** v prvním běhu kurzu pro platformu micro:bit.
  - Výukové video Martina Dostála vysvětlující princip návrhu stavového automatu: [YouTube – Stavové automaty](https://www.youtube.com/watch?v=NJkbWeEMMuw).
  - Portaci na **Pico:ed v2** (CircuitPython), rozšíření o přímé přechody mezi stavy, třídu `Step` (jednorázové kroky) a integraci s knihovnou `Timer`/`Period` zpracoval **Jan Chaloupek**.

---

## 4. Přehled PlantUML diagramů v `docs/diagrams/`

| Soubor | Popis komponenty |
|---|---|
| [`robot.puml`](diagrams/robot.puml) | Fasáda `JoyCarRobot` a integrace všech periferií |
| [`motion.puml`](diagrams/motion.puml) | Kinematika, třídy `Wheel`, `Wheels`, `CalibrateFactors`, budiče `PCA9633` a `PCA9685` |
| [`sensors.puml`](diagrams/sensors.puml) | Třída `Sensors` a strategie pro 2–6 čidel (`LineTracker2` až `LineTracker6`) |
| [`lcd.puml`](diagrams/lcd.puml) | Alfanumerický displej `TextDisplay` s protokolem HD44780 a řízením podsvícení |
| [`sonar.puml`](diagrams/sonar.puml) | Ultrazvukový senzor vzdálenosti `Sonar` (vzdálenost v metrech [m]) |
| [`sm.puml`](diagrams/sm.puml) | Stavový automat (`CPU`, `Task`, `Step`, `AbstractSM`, `CrossRoadsSM`) |

---

## 5. Jak generovat a prohlížet diagramy

1. Ve VS Code s nainstalovaným rozšířením **PlantUML** stačí otevřít libovolný soubor `.puml` a stisknout `Alt + D` pro zobrazení náhledu.
2. K exportu do PNG lze použít příkaz:
   ```bash
   plantuml docs/diagrams/*.puml
   ```
