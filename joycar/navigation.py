"""
navigation.py – Stavový automat pro navigaci křižovatkami na robotovi JoyCar.

Vzorový výukový modul pro studenty:
-----------------------------------
Tento modul spojuje stavový automat (`AbstractSM`), plánovač `CPU`, senzory a podvozek
do komplexní autonomní mise: robot má projet trasu složenou z posloupnosti křižovatek.

Doporučené studijní materiály (repozitář pomůcek):
- https://github.com/JanChaloupek/pomucky/blob/main/superloop.md – Proč je stavový automat ideální pro navigaci bez blokování
- https://github.com/JanChaloupek/pomucky/blob/main/compare_tick_function.md – Stabilní časování stavů pomocí ticks_ms()

Fyzikální princip manévru na křižovatce:
---------------------------------------
1. SLEDOVÁNÍ ČÁRY (sleduj_caru):
   Robot jede proporcionálně po čáře. Jakmile všechny přední senzory zachytí příčnou čáru,
   jde o křižovatku.
2. ZASTAVENÍ NA STOP-ČÁŘE (krizovatka):
   Robot zabrzdí, rozsvítí brzdová světla a vyčte z plánu `Commands`, kam má jet.
3. POPOJETÍ DO STŘEDU (popojed):
   Protože senzory jsou cca 5 cm před osou otáčení kol, robot musí kousek popojet rovně,
   aby se osa kol ocitla přímo nad křížením čar.
4. OTOČENÍ NA NOVOU ČÁRU (zatoc):
   Robot rotuje na místě se zapnutým blinkrem. Aby okamžitě nechytil starou čáru, ze které
   přijel, časovač `turnErrorTimer` (400 ms) ignoruje čtení senzorů. Teprve po odtočení
   začne hledat novou čáru. Jakmile ji střední senzor najde, pokračuje se jízdou.
"""

from joycar.sm import AbstractSM, Task, Step
from utils.log import log
from joycar.robot import JoyCarRobot
from joycar.sensors import LineSituationEnum
from joycar.direction import DirectionEnum
from joycar.lights import BeamsEnum
from joycar.display import display


class Commands:
    """
    Správce navigačního itineráře (plánu jízdy).

    Ukládá seznam instrukcí, kterými se robot řídí na jednotlivých křižovatkách:
    např. [FORWARD, LEFT, FORWARD, RIGHT].
    """

    def __init__(self, commandsList: list = None) -> None:
        """
        Args:
            commandsList (list|None): Seznam směrů (DirectionEnum nebo řetězce 'forward', 'left', 'right').
        """
        if commandsList is None:
            # Výchozí testovací okruh (jízda dokola s odbočením vlevo)
            self._list = [
                DirectionEnum.FORWARD,
                DirectionEnum.LEFT,
                DirectionEnum.FORWARD,
                DirectionEnum.LEFT,
                DirectionEnum.FORWARD,
                DirectionEnum.LEFT,
                DirectionEnum.FORWARD,
                DirectionEnum.LEFT,
            ]
        else:
            self._list = list(commandsList)

        self._index = 0

    def get(self):
        """Vrátí aktuální příkaz pro nadcházející křižovatku nebo None, pokud je trasa u konce."""
        if 0 <= self._index < len(self._list):
            return self._list[self._index]
        return None

    def next(self) -> None:
        """Posune ukazatel na další příkaz na trase."""
        self._index += 1

    def reset(self) -> None:
        """Resetuje itinerář na začátek trasy."""
        self._index = 0

    def __len__(self) -> int:
        return len(self._list)


class CrossRoadsSM(AbstractSM):
    """
    Stavový automat pro projetí trasy složené z křižovatek.

    Stavy automatu:
    - start       : Inicializace, zobrazení ikony 's', čekání na spuštění.
    - nastartuj   : Rozsvícení potkávacích světel, přechod do jízdy.
    - sleduj_caru : Proporcionální jízda po čáře, detekce příčné křižovatky.
    - krizovatka  : Zastavení na křižovatce, načtení příkazu z Commands.
    - popojed     : Předsunutí středu otáčení do středu křižovatky.
    - zatoc       : Otáčení se zapnutým blinkrem, dokud nechytíme novou čáru.
    - ztracen     : Záchranný stav při sjetí z trati (STOP + ikona 'x').
    - end         : Úspěšné dokončení celé trasy (STOP + ikona 'E').
    """

    STEP_nastartuj  = Step('nastartuj', tick_time=500)
    TASK_sledujCaru = Task('sleduj_caru', tick_time=20)
    STEP_krizovatka = Step('krizovatka', tick_time=500)
    TASK_popojed    = Task('popojed', tick_time=10)
    TASK_zatoc      = Task('zatoc', tick_time=10)
    STEP_ztracen    = Step('ztracen', tick_time=1000)

    def __init__(self, robot: JoyCarRobot, commands: Commands = None, tasks=None, tick_time=None) -> None:
        """
        Args:
            robot (JoyCarRobot): Instance robota, kterého automat řídí.
            commands (Commands|None): Plán trasy. Pokud None, použije se výchozí okruh.
        """
        self.robot = robot
        self.commands = commands if commands is not None else Commands()
        self.currentCommand = None
        self.history = []

        super().__init__(tasks, tick_time)

    # -------------------------------------------------------------------------
    # Stav 1: START
    # -------------------------------------------------------------------------
    def __start__init(self) -> None:
        display.drive_mode('s')
        self.history.append('start')
        log.info("CrossRoadsSM: start")

    def __start(self) -> None:
        # Přechod do stavu nastartování
        self.nextTask(self.STEP_nastartuj)

    # -------------------------------------------------------------------------
    # Stav 2: NASTARTUJ
    # -------------------------------------------------------------------------
    def __nastartuj__init(self) -> None:
        self.robot.lights.mainBeams = BeamsEnum.DIPPED
        display.drive_mode('|')
        self.history.append('nastartuj')
        log.info("CrossRoadsSM: nastartuj (rozsviceni potkavacich svetel)")

    def __nastartuj(self) -> None:
        # Po nastartování přecházíme do sledování čáry
        self.nextTask(self.TASK_sledujCaru)

    # -------------------------------------------------------------------------
    # Stav 3: SLEDUJ ČÁRU
    # -------------------------------------------------------------------------
    def __sleduj_caru__init(self) -> None:
        display.drive_mode('|')
        self.history.append('sleduj_caru')
        log.info("CrossRoadsSM: sleduj_caru")

        # Pokud už nemáme žádný další příkaz v itineráři, cíl je splněn!
        if self.commands.get() is None:
            self.endTask()

    def __sleduj_caru(self) -> None:
        situation = self.robot.getSituationLine()

        if situation == LineSituationEnum.CROSSROADS:
            # Dorazili jsme na křižovatku
            self.nextTask(self.STEP_krizovatka)
        elif situation == LineSituationEnum.LINE:
            # Běžná čára -> jedeme
            self.robot.rideLine(baseSpeed=0.2, turnGain=0.4)
        else:
            # Čára byla ztracena na dobu delší než toleranční okno
            self.nextTask(self.STEP_ztracen)

    # -------------------------------------------------------------------------
    # Stav 4: KŘIŽOVATKA (ZASTAVENÍ NA ČÁŘE)
    # -------------------------------------------------------------------------
    def __krizovatka__init(self) -> None:
        display.drive_mode('I+')
        self.robot.stop()
        self.currentCommand = self.commands.get()
        self.commands.next()
        self.history.append(f'krizovatka_{self.currentCommand}')
        log.info(f"CrossRoadsSM: krizovatka! Prikaz: {self.currentCommand}")

    def __krizovatka(self) -> None:
        # Po krátké pauze přejdeme k popojetí
        self.nextTask(self.TASK_popojed)

    # -------------------------------------------------------------------------
    # Stav 5: POPOJED (VYCENTROVÁNÍ STŘEDU OTÁČENÍ)
    # -------------------------------------------------------------------------
    def __popojed__init(self) -> None:
        display.drive_mode('_')
        self.robot.exitCrossRoads_start(timeoutMs=300)
        self.history.append('popojed')
        log.debug("CrossRoadsSM: popojed (vycentrovani osy otaceni)")

    def __popojed(self) -> None:
        done = self.robot.exitCrossRoads(self.currentCommand, forward=0.15)
        if done:
            # Pokud je příkaz jet rovně, nemusíme točit -> pokračujeme ve sledování
            if self.currentCommand in (DirectionEnum.FORWARD, "forward", 3):
                self.nextTask(self.TASK_sledujCaru)
            else:
                self.nextTask(self.TASK_zatoc)

    # -------------------------------------------------------------------------
    # Stav 6: ZATOČ (OTÁČENÍ NA MÍSTĚ NA NOVOU ČÁRU)
    # -------------------------------------------------------------------------
    def __zatoc__init(self) -> None:
        if self.currentCommand in (DirectionEnum.LEFT, "left", 1):
            display.drive_mode('TL')
        else:
            display.drive_mode('TR')

        self.robot.turningToLine_start(timeoutMs=350)
        self.history.append('zatoc')
        log.info(f"CrossRoadsSM: zatoc ({self.currentCommand})")

    def __zatoc(self) -> None:
        done = self.robot.turningToLine(self.currentCommand, angularSpeed=1.2)
        if done:
            # Čára úspěšně chycena -> vracíme se k jízdě
            self.nextTask(self.TASK_sledujCaru)

    # -------------------------------------------------------------------------
    # Stav 7: ZTRACEN (NOUZE)
    # -------------------------------------------------------------------------
    def __ztracen__init(self) -> None:
        display.drive_mode('x')
        self.robot.stop()
        self.robot.lights.off()
        self.history.append('ztracen')
        log.error("CrossRoadsSM: cara definitivne ztracena!")

    def __ztracen(self) -> None:
        # Končíme se selháním
        self.failureTask()

    # -------------------------------------------------------------------------
    # Stav 8: KONEC (ÚSPĚCH)
    # -------------------------------------------------------------------------
    def __end__init(self) -> None:
        display.drive_mode('E')
        self.robot.stop()
        self.history.append('end')
        log.info("CrossRoadsSM: trasa uspesne dokoncena (end)!")
