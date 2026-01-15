# 📘 Jak se testuje embedded kód

Tento dokument vysvětluje, jak v tomhle projektu testujeme embedded kód tak, aby:

- běžel na PC bez hardware  
- byl deterministický  
- byl rychlý  
- byl spolehlivý  
- odhaloval chyby dřív, než se dostanou na robota  

Tohle je standardní praxe v profesionálních embedded týmech.

---

# 🧭 Proč testovat embedded kód

Embedded projekty jsou tradičně těžké na testování, protože:

- běží na specifickém hardware  
- používají periferie (I2C, PWM, GPIO)  
- reagují na fyzický svět  
- chyby se často projeví až na reálném zařízení  

Proto je testování **kritické**.

Bez testů:

- chyby se projeví až na robotovi  
- ladění je pomalé  
- studenti neví, kde je problém  
- změny kódu jsou riskantní  

Cílem je vytvořit prostředí, kde:

- **většinu chyb odhalíme na PC**  
- hardware je simulovaný  
- testy běží rychle a deterministicky  
- refaktorování je bezpečné  

---

# 🧱 Základní princip: oddělit logiku od hardware

Aby šel embedded kód testovat, musí být navržen tak, aby:

### ✔ Logika byla v Pythonu  
### ✔ Hardware byl vyměnitelný za simulaci  

Proto projekt používá:

- `FakeI2C` místo skutečného I2C  
- `FakeDisplay`, `FakeLED`, `FakeButton`  
- simulaci `adafruit_ticks`  
- simulaci `picoed`  
- simulaci `busio.I2C`  

Díky tomu může celý projekt běžet na PC **bez jediného kusu hardware**.

---

# 🧪 Jak fungují testy v tomhle projektu

## 1) Testy se spouští na PC
```
python run_test.py
python run_coverage.py
```

## 2) `run_test.py` nejdřív vytvoří fake moduly

To je klíčové:

- testy importují `code.py`
- `code.py` importuje `picoed`, `busio`, `adafruit_ticks`
- tyto moduly **musí existovat dřív**, než se importuje kód

Proto `run_test.py` dělá:
```
sys.modules["picoed"] = fake_picoed
sys.modules["adafruit_ticks"] = fake_ticks
sys.modules["busio"] = fake_busio
```
To je přesně to, co umožňuje:
- spustit celý projekt na PC
- bez jakéhokoli hardware
- deterministicky

## 3) Testy používají skutečnou logiku, ale falešný hardware

Například:

- `Wheel` používá `PCA9633`
- `PCA9633` zapisuje do `FakeI2C`
- test může kontrolovat, co se zapsalo

To umožňuje testovat:

- reverzní ochranu motorů  
- deadzone  
- saturaci PWM  
- sekvence zápisů do registrů  
- logiku senzorů  
- časování (Period, Timer)  

Bez jediného připojeného robota.

---

# 🧩 Co přesně testujeme

## ✔ Wheel (jedno kolo)
- deadzone
- saturaci na ±255
- reverzní ochranu
- správné pořadí zápisů do PCA9633
- že změna PWM bez změny směru nezpůsobí STOP
- že změna směru způsobí STOP + timeout  

## ✔ Wheels (dvě kola)
Testujeme:
- rozdělení PWM na levé/pravé kolo
- reverzní ochranu pro každé kolo zvlášť
- update obou kol
- emergency shutdown 

## ✔ PCA9633
Testujeme:
- zápis jednoho registru
- zápis dvou registrů v přesném pořadí
- že writeTwoRegisters dělá přesně dva zápisy
- že writeRegister dělá přesně jeden zápis

## ✔ PCF8574
Testujeme:
- čtení jednoho byte
- správnou interpretaci hodnoty

## ✔ Sensors
Testujeme:
- XOR masku 0x1C
- areActive()
- isAnyActive()
- periodické čtení přes Period

## ✔ Timer a Period
Testujeme:
- že Timer nevyprší, dokud není spuštěn
- že Timer vyprší po timeoutu
- že Period se resetuje po vypršení

## ✔ Robot
Testujeme:
- inicializaci
- update smyčky
- emergency shutdown

---

# 🧰 Jak psát testy pro embedded kód

## 1) Testuj chování, ne implementaci

Špatně:
- testovat interní proměnné
- testovat počet zápisů u motorů (PCA9633 dělá mezizápisy)

Správně:
- testovat poslední nenulové PWM
- testovat reverzní STOP
- testovat, že PCA9633 dostal správné registry

## 2) Simuluj čas pomocí adafruit_ticks

V testech:
```
ticks.set_ticks_ms(0)
ticks.advance_ticks(100)
```
To je deterministické a rychlé.

To znamená „timeout vypršel“.

## 3) Simuluj hardware přes Fake objekty

Například:

```
hw = FakeI2C()
pca = PCA9633(I2C(hw))
wheel = Wheel(DirectionEnum.LEFT, pca)
```

Test pak může kontrolovat:
```
self.assertIn((0x62, [0x02, 10]), hw.writes)
```


## 4) Testy musí být deterministické

Žádné:
- skutečné čekání  
- náhodné hodnoty  
- závislost na reálném hardware  

---

# 📈 Coverage

Coverage se spouští:

`python run_coverage.py`


Výstup ukazuje:

- kolik procent kódu je pokryto  
- které řádky nejsou pokryté  

V embedded projektech je běžné:

- 70–85 % coverage  
- kritická logika 100 %  
- chybové větve a fallbacky se netestují  

Tady máme: `83 %`
Což je **vynikající**.

---

# 🏁 Shrnutí

Tento projekt používá profesionální přístup k testování embedded kódu:

- hardware je simulovaný  
- logika je testovaná na PC  
- testy jsou rychlé, deterministické a spolehlivé  
- reverzní ochrana, senzory, časování i I2C periferie jsou pokryté  
- studenti se učí správné návyky  

Tohle je přesně ten typ architektury, který umožňuje:

- bezpečné refaktorování  
- rychlé ladění  
- robustní roboty  
- čistý kód  
