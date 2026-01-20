# 📘 Superloop — Instruktorská verze

Tento dokument obsahuje:
- výukové cíle  
- doporučené postupy  
- vysvětlení metafor  
- pedagogické poznámky  
- řešení úkolů  
- upozornění na typické studentské chyby  

Studentská verze worksheetu je samostatná.  
Toto je metodický doplněk pro instruktory.

---

# 🎯 Výukové cíle

Student by měl po lekci:

- chápat princip superloopu  
- vědět, proč `sleep()` blokuje celý robot  
- umět použít `monotonic()` a `Timer`  
- umět psát komponenty s metodou `update()`  
- chápat, že superloop je „ruční asyncio“  
- umět přidat více úloh do jedné smyčky  
- umět vytvořit jednoduchý stavový automat  

---

# 🍳 1) Metafora: kuchař v restauraci  
**Instruktorská poznámka:**  
Tahle metafora funguje výborně, protože studenti intuitivně chápou, že kuchař nemůže dělat dvě věci najednou, ale může mezi nimi rychle přepínat.

Důležité body k vysvětlení:

- kuchař = CPU  
- jednotlivé úkoly = komponenty robota  
- rychlé přepínání = superloop  
- žádné paralelní vaření = žádná vlákna  

**Cíl:**  
Student pochopí, že robot nedělá věci paralelně, ale sekvenčně a rychle.

---

# 🎻 2) Metafora: robot jako orchestr  
**Instruktorská poznámka:**  
Tahle metafora pomáhá pochopit objektový návrh.

- dirigent = superloop  
- hudebníci = komponenty  
- každý hudebník má vlastní part = vlastní `update()`  
- dirigent jen říká „hrajem dál“ = volání `robot.update()`  

**Cíl:**  
Student pochopí, proč každá komponenta má vlastní `update()`.

---

# 🛑 3) Klíčová myšlenka: „Nikdy nic neblokuj“  
**Instruktorská poznámka:**  
Toto je nejdůležitější část celé lekce.  
Studenti mají tendenci používat `sleep()`, protože je to jednoduché.

Doporučený postup:

1. Nechte studenty napsat kód s `sleep()`.  
2. Nechte je pozorovat, že robot „zamrzne“.  
3. Vysvětlete, že `sleep()` blokuje celý superloop.  
4. Ukažte, jak to opravit pomocí `monotonic()` nebo `Timer`.

**Cíl:**  
Student pochopí, že `sleep()` je v robotice nepoužitelný.

---

# ⏱️ 4) Časování pomocí monotonic()  
**Instruktorská poznámka:**  
Studenti často nechápou, proč nepoužíváme `time.time()`.  
Vysvětlete:

- `monotonic()` nikdy nejde zpět  
- není ovlivněn změnou systémového času  
- je ideální pro časování v superloopu  

**Cíl:**  
Student umí napsat neblokující časovač.

---

# 🧩 5) Objekt Timer  
**Instruktorská poznámka:**  
Timer je klíčový nástroj pro čistý objektový návrh.  
Studenti ho rychle pochopí, protože:

- je malý  
- je jednoduchý  
- řeší konkrétní problém  

Důležité zdůraznit:

- Timer není „alarm“  
- Timer nečeká  
- Timer jen říká „už uplynul čas?“  

**Cíl:**  
Student umí použít Timer v komponentách.

---

# 🔁 6) Objektový superloop  
**Instruktorská poznámka:**  
Tady se propojí všechny předchozí části.

Důležité body:

- každá komponenta má vlastní `update()`  
- robot má jen `update()`, které volá ostatní  
- superloop je extrémně jednoduchý  
- komponenty jsou nezávislé a snadno testovatelné  

**Cíl:**  
Student umí navrhnout robota jako sadu komponent.

---

# 🔌 7) Přirovnání k asyncio  
**Instruktorská poznámka:**  
Toto je volitelné, ale velmi užitečné pro pokročilejší studenty.

Vysvětlete:

- asyncio používá `await`  
- superloop používá rychlé návraty z `update()`  
- Timer je ekvivalent `await asyncio.sleep()`  
- superloop je vlastně ruční event loop  

**Cíl:**  
Student chápe, že superloop je obecný princip, ne trik.

---

# 🧪 8) Cvičení — Instruktorská doporučení

### Úkol 1–3  
Doporučte studentům:

- začít s jednoduchým intervalem  
- testovat každou komponentu samostatně  
- přidávat komponenty postupně  

### Úkol 4  
Důležité:  
Studenti často zapomenou volat všechny komponenty v `Robot.update()`.

### Úkol 5  
Nechte studenty pozorovat chování robota.  
Je to silný moment, kdy pochopí blokování.

---

# 🚀 9) Pokročilé úkoly — Instruktorská doporučení

### Úkol A — LineFollower  
Cíl: pochopit spolupráci komponent.  
Doporučení:  
Upozorněte na závislosti (sensors, motors).

### Úkol B — Stavový automat  
Cíl: naučit studenty strukturovat chování robota.  
Doporučení:  
Začněte dvěma stavy, pak přidejte třetí.

### Úkol C — Watchdog  
Cíl: pochopit bezpečnostní mechanismy.

### Úkol D — FPSCounter  
Cíl: měřit výkon superloopu.

---

# 🏁 Shrnutí pro instruktory

- Superloop je základní koncept robotiky  
- Studenti ho pochopí nejlépe přes metafory  
- Největší problém je blokování (`sleep()`)  
- Timer je klíčový nástroj pro čistý návrh  
- Objektový styl s `update()` je ideální pro výuku  
- Pokročilé úkoly rozvíjejí hlubší porozumění  

Doporučení:  
Nechte studenty experimentovat.  
Superloop je koncept, který se nejlépe učí praxí.

