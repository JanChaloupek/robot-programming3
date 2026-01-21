"""
run_test.py – spouštěč unit testů s fake hardwarem

Tento skript umožňuje spouštět embedded kód na PC bez skutečného hardware.
Zajišťuje:

1) Přidání adresáře _stubs/ do sys.path
   → VS Code i testy mohou importovat fake moduly (board, neopixel, busio, …)

2) Přesměrování importů:
      import board
      import neopixel
      import digitalio
      import analogio
      import busio
      import pwmio
      import picoed
      import adafruit_ticks
      import time
   → na jejich fake verze v _stubs/

3) Deterministické časování přes _stubs/time.py a _stubs/adafruit_ticks.py

4) Barevný výstup unittest výsledků

Tento skript je klíčový pro:
- testování logiky bez hardware
- deterministické testy bez čekání
- kompatibilitu s CircuitPython API
"""

import sys
import os
import unittest
import importlib


# ---------------------------------------------------------
# 0) Přidat _stubs do sys.path
# ---------------------------------------------------------
BASE_DIR = os.path.dirname(__file__)
STUBS_DIR = os.path.join(BASE_DIR, "_stubs")
sys.path.insert(0, STUBS_DIR)

# ---------------------------------------------------------
# Helper: načti fake modul z _stubs a zaregistruj ho
# ---------------------------------------------------------
def load_fake(name: str):
    """
    Načte modul _stubs.<name> a zaregistruje ho jako <name>.

    Příklad:
        load_fake("board") → sys.modules["board"] = _stubs.board

    Tím se zajistí, že import board bude používat fake verzi.
    """
    module = importlib.import_module(f"_stubs.{name}")
    sys.modules[name] = module
    return module


# ---------------------------------------------------------
# 1) Přesměrování modulů na fake verze
# ---------------------------------------------------------

# Deterministické časování
load_fake("adafruit_ticks")

# Fake picoed (tlačítka, display, I2C…)
load_fake("picoed")

# Fake time (deterministický čas pro Timer/Period)
load_fake("time")

# Fake hardware moduly
load_fake("board")
load_fake("neopixel")
load_fake("digitalio")
load_fake("analogio")
load_fake("busio")
load_fake("pwmio")


# ---------------------------------------------------------
# 2) Barevný výstup testů
# ---------------------------------------------------------
class Color:
    RESET = "\033[0m"
    BOLD = "\033[1m"
    GREEN = "\033[92m"
    RED = "\033[91m"
    YELLOW = "\033[93m"
    CYAN = "\033[96m"


class ColorTextTestResult(unittest.TextTestResult):
    """
    Rozšířený výstup unittest výsledků s barvami.
    """
    def addSuccess(self, test):
        super().addSuccess(test)
        self.stream.write(f"{Color.GREEN}✔ PASS{Color.RESET} ")
        self.stream.writeln(f"{test}")

    def addFailure(self, test, err):
        super().addFailure(test, err)
        self.stream.write(f"{Color.RED}✘ FAIL{Color.RESET} ")
        self.stream.writeln(f"{test}")

    def addError(self, test, err):
        super().addError(test, err)
        self.stream.write(f"{Color.YELLOW}⚠ ERROR{Color.RESET} ")
        self.stream.writeln(f"{test}")


class ColorTextTestRunner(unittest.TextTestRunner):
    """
    Test runner používající barevné výsledky.
    """
    resultclass = ColorTextTestResult


# ---------------------------------------------------------
# 3) Hlavní funkce
# ---------------------------------------------------------
def main():
    """
    Najde všechny testy v adresáři tests/ a spustí je.
    """
    print(f"{Color.CYAN}{Color.BOLD}Running tests...{Color.RESET}")

    test_dir = os.path.join(os.path.dirname(__file__), "tests")
    loader = unittest.TestLoader()
    suite = loader.discover(test_dir)

    runner = ColorTextTestRunner(verbosity=2)
    result = runner.run(suite)

    if result.wasSuccessful():
        print(f"\n{Color.GREEN}{Color.BOLD}ALL TESTS PASSED ✔{Color.RESET}")
    else:
        print(f"\n{Color.RED}{Color.BOLD}SOME TESTS FAILED ✘{Color.RESET}")

    sys.exit(not result.wasSuccessful())


if __name__ == "__main__":
    main()
