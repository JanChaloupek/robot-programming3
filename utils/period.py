"""
period.py – periodický časovač.

Period funguje jako Timer, ale po timeoutu se automaticky restartuje.
Vhodné pro libovolné projekty v CircuitPythonu.
"""

from utils import Timer


class Period(Timer):
    """
    Periodický časovač – po timeoutu se automaticky restartuje.

    Chování:
        - ready() vrací True pokud timeout vypršel a zároveň restartuje časovač.
        - is_timeout(...) zůstává čistým testem bez efektů (zděděno z Timer).
    """

    def ready(self) -> bool:
        """
        Vrátí True, pokud nastal čas události, a restartuje časovač.

        Použití:
            p = Period(timeout_ms=500)
            if p.ready():
                # vykonej periodickou akci
        """
        if self.is_timeout():
            self.restart()
            return True
        return False
