"""
test_sm.py – Testy pro stavový automat (SM) a plánovač CPU.

Výukový modul:
Ukazuje studentům, jak testovat stavový automat v deterministickém simulovaném čase.
"""

import unittest
from utils.sm import CPU, Task, Step, AbstractSM
import _fake.adafruit_ticks as fake_ticks


class DummySM(AbstractSM):
    """
    Jednoduchý testovací stavový automat.
    
    Cesta stavů:
    1. start -> přechází na STEP_init
    2. STEP_init -> jednorázový krok, přejde na TASK_count
    3. TASK_count -> opakuje se 3x a pak zavolá endTask()
    4. end -> dokončeno úspěšně
    """

    STEP_init = Step('priprav')
    TASK_count = Task('pocitej', tick_time=50)

    def __init__(self, tasks=None, tick_time=None):
        super().__init__(tasks, tick_time)
        self.log_history = []
        self.counter = 0

    def __start(self):
        self.log_history.append('start')
        self.nextTask(self.STEP_init)

    def __priprav__init(self):
        self.log_history.append('priprav__init')

    def __priprav(self):
        self.log_history.append('priprav_run')
        self.nextTask(self.TASK_count)

    def __priprav__done(self):
        self.log_history.append('priprav__done')

    def __pocitej(self):
        self.counter += 1
        self.log_history.append(f'pocitej_{self.counter}')
        if self.counter >= 3:
            self.endTask()

    def __end__init(self):
        self.log_history.append('end')


class TestStateMachine(unittest.TestCase):
    """Testovací sada pro ověření chování FSM a plánovače CPU."""

    def setUp(self):
        CPU.clear()
        fake_ticks.set_ticks_ms(0)

    def test_sm_lifecycle(self):
        """Ověří kompletní životní cyklus stavů (__init, tělo, __done, úspěšné ukončení)."""
        sm = DummySM()
        CPU.add(sm)

        self.assertTrue(CPU.existSM())
        self.assertIsNone(sm.success)

        # Procházíme tiky v čase
        for _ in range(25):
            fake_ticks.advance_ticks(50)
            CPU.tick()
            if not CPU.existSM():
                break

        # Ověříme, že všechny fáze proběhly ve správném pořadí
        self.assertEqual(sm.log_history, [
            'start',
            'priprav__init',
            'priprav_run',
            'priprav__done',
            'pocitej_1',
            'pocitej_2',
            'pocitej_3',
            'end'
        ])

        # Ověříme, že automat skončil úspěšně a byl odstraněn z CPU
        self.assertTrue(sm.success)
        self.assertFalse(CPU.existSM(), "Dokončený automat musí být vyřazen z CPU")

    def test_failure_handling(self):
        """Ověří, že failureTask() správně ukončí automat se stavem success = False."""
        class FailSM(AbstractSM):
            STEP_fail = Step('spadni')
            def __start(self):
                self.nextTask(self.STEP_fail)
            def __spadni(self):
                self.failureTask()

        sm = FailSM()
        CPU.add(sm)

        for _ in range(10):
            CPU.tick()
            if not CPU.existSM():
                break

        self.assertFalse(sm.success)
        self.assertFalse(CPU.existSM())

    def test_cpu_hierarchical_parent_child(self):
        """Ověří vazbu mezi rodičovským a dceřiným automatem v CPU (parentOf)."""
        class ParentSM(AbstractSM):
            pass

        class ChildSM(AbstractSM):
            pass

        parent = ParentSM()
        CPU.add(parent)
        self.assertEqual(parent.cpu_no, 1)

        child = ChildSM()
        CPU.add(child, cpu_no_parent=parent.cpu_no)
        self.assertEqual(child.cpu_no, 2)

        # parentOf vrátí instanci rodiče
        self.assertIs(CPU.parentOf(child.cpu_no), parent)
        self.assertIsNone(CPU.parentOf(parent.cpu_no))
        self.assertIsNone(CPU.parentOf(999))

    def test_cpu_multiple_concurrent_sms(self):
        """Ověří paralelní běh dvou nezávislých stavových automatů."""
        class CountingSM(AbstractSM):
            TASK_work = Task('work', tick_time=50)

            def __init__(self, target):
                super().__init__()
                self.target = target
                self.count = 0

            def __start(self):
                self.nextTask(self.TASK_work)

            def __work(self):
                self.count += 1
                if self.count >= self.target:
                    self.endTask()

        sm1 = CountingSM(target=2)
        sm2 = CountingSM(target=4)
        CPU.add(sm1)
        CPU.add(sm2)

        self.assertEqual(len(CPU._CPU__Q), 2)

        # Procházíme tiky v čase
        for _ in range(25):
            fake_ticks.advance_ticks(50)
            CPU.tick()
            if not CPU.existSM():
                break

        self.assertTrue(sm1.success)
        self.assertTrue(sm2.success)
        self.assertFalse(CPU.existSM())

    def test_step_autonext_chaining(self):
        """Ověří, že třída Step s autoNext=True automaticky přechází na další krok ve frontě."""
        class ChainedSM(AbstractSM):
            STEP1 = Step('krok1')
            STEP2 = Step('krok2')

            def __init__(self):
                super().__init__(tasks=[self.STEP1, self.STEP2])
                self.history = []

            def __krok1(self):
                self.history.append('krok1_done')

            def __krok2(self):
                self.history.append('krok2_done')
                self.endTask()

        sm = ChainedSM()
        CPU.add(sm)

        for _ in range(10):
            fake_ticks.advance_ticks(50)
            CPU.tick()
            if not CPU.existSM():
                break

        self.assertEqual(sm.history, ['krok1_done', 'krok2_done'])
        self.assertTrue(sm.success)


if __name__ == "__main__":
    unittest.main()
