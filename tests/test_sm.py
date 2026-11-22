"""
test_sm.py – Testy pro stavový automat (SM) a plánovač CPU.

Výukový modul:
Ukazuje studentům, jak testovat stavový automat v deterministickém simulovaném čase.
"""

import unittest
from joycar.sm import CPU, Task, Step, AbstractSM
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


if __name__ == "__main__":
    unittest.main()
