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

Embedded projekty jsou tradičně považované za „těžko testovatelné“, protože:

- běží na specifickém hardware  
- používají periferie (I2C, PWM, GPIO)  
- reagují na fyzický svět  
- chyby se často projeví až na reálném zařízení  

Právě proto je testování **kritické**.

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
- simulaci `busio.I2C`  
- simulaci `picoed`  

Díky tomu může celý projekt běžet na PC **bez jediného kusu hardware**.

---

# 🧪 Jak fungují testy v tomhle projektu

## 1) Testy se spouští na PC

`python run_test.py`

nebo s coverage:

`python run_coverage.py`


## 2) `run_test.py` nejdřív vytvoří fake moduly

To je klíčové:

- testy importují `code.py`
- `code.py` importuje `picoed`, `busio`, `adafruit_ticks`
- tyto moduly **musí existovat dřív**, než se importuje kód

Proto se mocky registrují v `sys.modules` ještě před načtením testů.

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

## ✔ Logiku motorů (Wheel)
- deadzone  
- max limit  
- reverzní ochranu  
- bezpečné PWM  
- správné mapování PWM na registry  

## ✔ Logiku dvou motorů (Wheels)
- distribuci PWM  
- update obou kol  
- emergency shutdown  

## ✔ I2C periferie
- PCA9633 (PWM driver)
- PCF8574 (senzorový expander)

Testujeme:

- správné pořadí zápisů  
- správné registry  
- správné hodnoty  

## ✔ Senzory
- invertovanou logiku  
- masky  
- areActive / isAnyActive  
- periodické čtení  

## ✔ Časování
- Timer  
- Period  

## ✔ Robot jako celek
- inicializaci  
- update smyčky  
- emergency shutdown  

---

# 🧰 Jak psát testy pro embedded kód

## 1) Testuj chování, ne implementaci

Špatně:

- testovat konkrétní registry  
- testovat počet zápisů  
- testovat interní proměnné  

Správně:

- testovat, že PWM je správné  
- testovat, že reverzní ochrana funguje  
- testovat, že senzory vrací správné hodnoty  
- testovat, že emergency shutdown zastaví kola  

## 2) Simuluj čas

Timer a Period používají `ticks_ms`.  
V testech se čas simuluje takto:

```
timer._startTime = 0
timer.timeout_ms = -1
```


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
self.assertEqual(hw.writes[-1], (0x62, [3, 100]))
```


## 4) Testy musí být deterministické

Žádné:

- náhodné hodnoty  
- skutečné časové čekání  
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

Tady máme: `81 %`


Což je **vynikající**.

---

# 🏁 Shrnutí

Tento projekt ukazuje profesionální přístup k testování embedded kódu:

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
