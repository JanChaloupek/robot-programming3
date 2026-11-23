"""
sm.py – Stavový automat (State Machine) a dispečer CPU pro neblokující řízení robota.

Vzorový výukový modul pro studenty:
-----------------------------------
Tento modul implementuje vzor stavového automatu (Finite State Machine – FSM)
v kombinaci s kooperativním plánovačem (CPU dispečer).

Historie a autorství jádra stavového automatu:
----------------------------------------------
- Původní architekturu a jádro stavového automatu (třídy CPU, Task, AbstractSM a Period)
  vytvořil student Martin Dostál v prvním běhu kurzu pro platformu micro:bit.
- Výukové video Martina Dostála vysvětlující princip stavového automatu:
  https://www.youtube.com/watch?v=NJkbWeEMMuw
- Upravenou verzi pro Pico:ed v2 (CircuitPython) s přímými přechody mezi stavy,
  podporou kroků (Step) a integrací s neblokujícím časovačem Timer/Period upravil Jan Chaloupek.

Doporučené studijní materiály (repozitář pomůcek):
- https://github.com/JanChaloupek/pomucky/blob/main/superloop.md – Proč robot nesmí používat sleep() a jak funguje superloop
- https://github.com/JanChaloupek/pomucky/blob/main/sleep.md – Blokování runtime a proč používat neblokující architekturu
- https://github.com/JanChaloupek/pomucky/blob/main/compare_tick_function.md – Časování bez ztráty přesnosti s adafruit_ticks

Proč používáme stavový automat namísto sekvenčního kódu se sleep()?
-------------------------------------------------------------------
Představte si křižovatku: robot musí jet rovně, sledovat čáru, hlídat překážky
a u toho blikat blinkrem. Pokud by program napsal začátečník se sleep():
    zapni_blinkr()
    sleep(0.5)      # <--- ZDE ROBOT SLEPĚ JEDE A IGNORUJE SENZORY!
    vypni_blinkr()

Ve stavovém automatu každá akce probíhá v malých, neblokujících krocích:
1. V každém cyklu hlavní smyčky zavoláme `CPU.tick()`.
2. Každý registrovaný stavový automat (`AbstractSM`) zkontroluje, zda uplynul jeho časový krok.
3. Pokud ano, provede tělo aktuálního stavu a okamžitě vrátí řízení ostatním subsystémům.

Hierarchie a životní cyklus:
----------------------------
- CPU:
    Centrální plánovač (dispečer), který drží seznam aktivních stavových automatů
    a v každém cyklu jim předává řízení pomocí CPU.tick().

- Task (Stav):
    Trvalý stav (např. sledování čáry), který běží opakovaně v zadané periodě (tickTime),
    dokud sám nerozhodne o přechodu na jiný stav pomocí `self.nextTask()`.

- Step (Krok):
    Potomek třídy Task s vlastností `autoNext = True`. Vykoná se jednou a po dokončení
    se automaticky přepne na následující stav ze zásobníku (např. krátké zatroubení).

- AbstractSM (Základní automat):
    Poskytuje tři fáze pro každý stav:
    - __{nazev}__init() : Spustí se jednorázově PŘED vstupem do stavu (nastavení podmínek).
    - __{nazev}()       : Hlavní tělo stavu (vykonává se opakovaně nebo jednorázově).
    - __{nazev}__done() : Spustí se jednorázově PO opuštění stavu (úklid, např. zhasnutí světel).
"""

from adafruit_ticks import ticks_ms
from utils.period import Period
from utils.log import log


class CPU:
    """
    Centrální dispečer a plánovač stavových automatů.

    Umožňuje běžet několika stavovým automatům současně v jednovláknovém
    prostředí (kooperativní multitasking / superloop).
    """
    __NO = 0
    __Q = {}

    @staticmethod
    def add(sm: 'AbstractSM', cpu_no_parent: int = None) -> 'AbstractSM':
        """
        Zaregistruje nový stavový automat do fronty procesoru a spustí jej.

        Args:
            sm (AbstractSM): Instance stavového automatu.
            cpu_no_parent (int|None): Číslo rodičovského automatu (pokud jde o vnořený proces).

        Returns:
            AbstractSM: Zaregistrovaný automat.
        """
        CPU.__NO += 1
        sm.cpu_no = CPU.__NO
        CPU.__Q[CPU.__NO] = [sm, cpu_no_parent]
        sm.run()
        return sm

    @staticmethod
    def parentOf(cpu_no: int) -> 'AbstractSM | None':
        """Vrátí rodičovský stavový automat pro dané ID procesu."""
        if cpu_no not in CPU.__Q:
            return None
        cpu_no_parent = CPU.__Q[cpu_no][1]
        if cpu_no_parent is None or cpu_no_parent not in CPU.__Q:
            return None
        return CPU.__Q[cpu_no_parent][0]

    @staticmethod
    def remove(cpu_no: int) -> None:
        """Odstraní automat z fronty procesoru."""
        if cpu_no in CPU.__Q:
            del CPU.__Q[cpu_no]

    @staticmethod
    def tick() -> None:
        """
        Vykoná jeden takt všech běžících stavových automatů.

        Důležité pro studenty:
        Používáme `list(CPU.__Q.values())`, protože během tiku může některý
        automat dokončit svůj běh a zavolat CPU.remove(), což by při přímé
        iteraci přes slovník způsobilo chybu běhu (dictionary changed size during iteration).
        """
        for item in list(CPU.__Q.values()):
            item[0].tick()

    @staticmethod
    def existSM() -> bool:
        """Vrací True, pokud je v plánovači alespoň jeden aktivní stavový automat."""
        return len(CPU.__Q) > 0

    @staticmethod
    def clear() -> None:
        """Vyčistí frontu všech automatů (užitečné např. před spuštěním testů)."""
        CPU.__Q.clear()
        CPU.__NO = 0


class Task:
    """
    Reprezentuje stav stavového automatu.

    Běží opakovaně v intervalech zadaných v tick_time, dokud není explicitně
    přepnut metodou `nextTask()`, `endTask()` nebo `failureTask()`.
    """

    def __init__(self, name: str, tick_time: int = None) -> None:
        """
        Args:
            name (str): Název stavu (např. 'sleduj_caru'). Metody v automatu pak
                budou mít název `__{name}`, `__{name}__init` a `__{name}__done`.
            tick_time (int|None): Perioda volání těla stavu v ms. Pokud None,
                použije se výchozí perioda automatu.
        """
        self.id = None
        self.name = name
        self.tickTime = tick_time
        self.autoNext = False

    def __str__(self) -> str:
        return self.name


class Step(Task):
    """
    Jednorázový krok ve stavovém automatu.

    Po vykonání své hlavní metody se automaticky přepne na další úlohu ze zásobníku
    (autoNext = True). Vhodné pro krátké akce typu rozsvícení LED, zapnutí zvuku,
    záznam do odometrie apod.
    """

    def __init__(self, name: str, tick_time: int = None) -> None:
        super().__init__(name, tick_time)
        self.autoNext = True


class AbstractSM:
    """
    Abstraktní základní třída pro stavové automaty robota.

    Podporuje:
    - Zásobník úloh (stack) a sekvenční procházení.
    - Fázované volání stavu: __init -> periodický běh -> __done.
    - Ošetření úspěšného konce (end) i selhání (failure).
    - Bezpečnou vazbu na rodičovský automat (hierarchické automaty).
    """

    # Vestavěné výchozí stavy přítomné v každém automatu
    __state_start = Task('start')
    __state_end = Step('end')
    __state_failure = Step('failure')

    INIT_SUFFIX = '__init'
    DONE_SUFFIX = '__done'

    def __init__(self, tasks: list[Task] = None, tick_time_default: int = None) -> None:
        """
        Inicializace stavového automatu.

        Args:
            tasks (list[Task]|None): Počáteční fronta úloh/kroků. Pokud není zadána,
                začíná se stavem 'start'.
            tick_time_default (int|None): Výchozí perioda v milisekundách mezi tiky.
        """
        self.success = None
        self._period = Period()
        self._stack = []
        self._curTask = None
        self._nextTask = None
        self.cpu_no = None
        self._running = False
        self._tic = 0
        self.debug = False
        self.debugSKIP = False

        if not isinstance(tasks, list):
            tasks = [self.__state_start]
        self.setTasks(tasks, tick_time_default)

    # -------------------------------------------------------------------------
    # Vestavěné výchozí metody životního cyklu
    # -------------------------------------------------------------------------

    def __start(self) -> None:
        """Výchozí implementace startovního stavu – přejde na další krok."""
        self.nextTask()

    def __end(self) -> None:
        """Výchozí ukončení automatu s úspěchem (success = True)."""
        self._cleanSelf(True)

    def __failure(self) -> None:
        """Výchozí ukončení automatu s neúspěchem (success = False)."""
        self._cleanSelf(False)

    def _cleanSelf(self, success: bool) -> None:
        """Úklid automatu po dokončení a notifikace rodiče."""
        self.success = success
        status = 'success' if success else 'failure'
        log.info(f"SM: ({self.cpu_no}, {type(self).__name__}) {status}")
        if self.debug:
            print(f"({self.cpu_no}, {type(self).__name__}) {status}")

        parent = CPU.parentOf(self.cpu_no)
        if parent:
            parent.cpu_child_done(self.cpu_no)

        CPU.remove(self.cpu_no)

    def add2CPU(self, sm: 'AbstractSM') -> 'AbstractSM':
        """Přidá dceřiný automat do CPU a prováže jej s tímto automatem."""
        return CPU.add(sm, self.cpu_no)

    def cpu_child_done(self, cpu_no: int) -> None:
        """Zpětné volání vyvolané ve chvíli, kdy dceřiný automat dokončí svůj úkol."""
        pass

    def run(self) -> None:
        """Spustí běh automatu, aktivuje časovač a připraví první úlohu."""
        self._running = True
        self._period.startTimer()
        self.nextTask()

    def nextTask(self, task: Task = None, skipTimeout: bool = None) -> None:
        """
        Přepne na následující úlohu.

        Args:
            task (Task|None): Konkrétní úloha k přepnutí. Pokud je None,
                vybere se další úloha ze zásobníku.
            skipTimeout (bool|None): Zda přeskočit čekání a provést přechod ihned.
        """
        if skipTimeout is None:
            # Přeskočíme timeout, pokud aktuální úloha nebyla instance Step
            skipTimeout = not isinstance(self._curTask, Step)

        if skipTimeout:
            self._setPeriodTimeout(0)

        if task is not None:
            self._nextTask = task
            return

        if self._stack:
            self._nextTask = self._stack.pop(0)
            return

        # Pokud už žádná úloha nezbývá a automat ještě neskončil
        if self.success is None:
            self.endTask()

    def endTask(self) -> None:
        """Přepne automat do koncového stavu 'end'."""
        self._nextTask = self.__state_end
        self._setPeriodTimeout(0)

    def failureTask(self) -> None:
        """Přepne automat do chybového stavu 'failure'."""
        self._nextTask = self.__state_failure
        self._setPeriodTimeout(0)

    def startTask(self) -> None:
        """Přepne automat do počátečního stavu 'start'."""
        self._nextTask = self.__state_start
        self._setPeriodTimeout(0)

    def tick(self) -> None:
        """
        Vykoná jeden krok stavového automatu, pokud nastal čas periody.

        Vysvětlení pro studenty:
        Tato metoda je volána plánovačem CPU.tick(). Pokud časovač ještě nevypršel,
        metoda ihned skončí a nespotřebovává zbytečný procesorový čas.
        """
        if not self._running:
            return

        if self._period.isTime():
            # 1. Řešení přechodu na nový stav
            if self._nextTask is not None:
                # Pokud již máme běžící stav, nejprve zavoláme jeho úklid (__done)
                if self._curTask is not None:
                    self._callStep(self.DONE_SUFFIX)

                # Přepneme na nový stav
                self._curTask = self._nextTask
                self._nextTask = None
                self._tic += 1
                self._curTask.id = self._tic

                # Spustíme inicializaci nového stavu (__init) ihned
                self._setPeriodTimeout(0)
                self._callStep(self.INIT_SUFFIX)
                return

            # 2. Vykonání těla aktuálního stavu
            if self._curTask is not None:
                self._setPeriodTimeout(self._curTask.tickTime)
                self._callStep()

                # Pokud má stav nastaveno autoNext (Step) a nebyl definován jiný přechod
                if self._curTask.autoNext:
                    if self._nextTask is None:
                        self.nextTask()

    def setTasks(self, tasks: list[Task], tick_time_default: int) -> None:
        """Nastaví novou sadu úloh do zásobníku."""
        self._period.startTimer()
        self._tickTimeDefault = tick_time_default
        self._stack = tasks if isinstance(tasks, list) else []
        if self._running:
            self.nextTask()

    def _getMethod(self, task_name: str, suffix: str = ''):
        """
        Najde příslušnou metodu pro daný stav s ohledem na Python name mangling.

        Vysvětlení pro studenty:
        Pokud v Pythonu pojmenujete metodu se dvěma podtržítky uvnitř třídy
        (např. `def __krok(self):`), kompilátor ji automaticky přejmenuje
        na `_NazevTridy__krok`. Tato pomocná metoda bezpečně dohledá správnou
        funkci bez ohledu na to, zda student použije `__krok` nebo `_krok`.
        """
        candidates = [
            f"_{type(self).__name__}__{task_name}{suffix}",
            f"_AbstractSM__{task_name}{suffix}",
            f"__{task_name}{suffix}",
            f"_{task_name}{suffix}",
            f"{task_name}{suffix}",
        ]
        for cand in candidates:
            if hasattr(self, cand):
                return getattr(self, cand)
        return None

    def _callStep(self, suffix: str = '') -> None:
        """Vyvolá obslužnou metodu aktuálního stavu s daným sufixem (__init, __done nebo bez)."""
        fce = self._getMethod(self._curTask.name, suffix)
        if fce is not None:
            log.debug(f"SM: ({self.cpu_no}, {type(self).__name__}) __{self._curTask.name}{suffix}")
            if self.debug:
                print(f"({self.cpu_no}, {type(self).__name__})", ticks_ms(), f"__{self._curTask.name}{suffix}")
            fce()
        else:
            if self.debugSKIP and suffix == '':
                log.debug(f"SM: ({self.cpu_no}, {type(self).__name__}) __{self._curTask.name}{suffix} --SKIP")
                print(f"({self.cpu_no}, {type(self).__name__})", ticks_ms(), f"__{self._curTask.name}{suffix}", '    --SKIP')

    def _setPeriodTimeout(self, timeout_ms: int | None) -> None:
        """Nastaví časový limit periody automatu."""
        if timeout_ms is None:
            timeout_ms = self._tickTimeDefault
        if timeout_ms is None:
            timeout_ms = 0
        self._period.timeout_ms = timeout_ms

    def setTickTime(self, tickTime: int) -> None:
        """Dynamicky změní periodu aktuálního stavu."""
        if self._curTask is not None:
            self._curTask.tickTime = tickTime
