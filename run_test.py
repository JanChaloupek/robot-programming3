"""
run_test.py – spouštěč unit testů s fake hardwarem
"""

import sys
import os
import importlib
import argparse


# ---------------------------------------------------------
# 0) Přidat _stubs do sys.path (bez duplicit)
# ---------------------------------------------------------
BASE_DIR = os.path.dirname(__file__)
STUBS_DIR = os.path.join(BASE_DIR, "_stubs")

if STUBS_DIR not in sys.path:
    sys.path.insert(0, STUBS_DIR)


# ---------------------------------------------------------
# Helper: načti fake modul z _fake a zaregistruj ho
# ---------------------------------------------------------
def load_fake(name: str):
    module = importlib.import_module(f"_fake.{name}")
    sys.modules[name] = module
    return module

# ---------------------------------------------------------
# 1) Přesměrování modulů na fake verze (správné pořadí!)
# ---------------------------------------------------------
ticks = load_fake("adafruit_ticks")
load_fake("time")

load_fake("board")
load_fake("digitalio")
load_fake("analogio")
load_fake("busio")
load_fake("pwmio")
load_fake("neopixel")

load_fake("picoed")


# ---------------------------------------------------------
# 2) Teprve teď importujeme unittest
# ---------------------------------------------------------
import unittest


# ---------------------------------------------------------
# 3) Barevný výstup testů
# ---------------------------------------------------------
class Color:
    RESET = "\033[0m"
    BOLD = "\033[1m"
    GREEN = "\033[92m"
    RED = "\033[91m"
    YELLOW = "\033[93m"
    CYAN = "\033[96m"


class ColorTextTestResult(unittest.TextTestResult):
    def startTest(self, test):
        # Reset ticks před každým testem
        ticks.set_ticks_ms(0)
        super().startTest(test)

    def addSuccess(self, test):
        super().addSuccess(test)
        self.stream.write(f"{Color.GREEN}✔ PASS{Color.RESET} ")
        self.stream.writeln(f"{Color.CYAN}{test}{Color.RESET}")

    def addFailure(self, test, err):
        super().addFailure(test, err)
        self.stream.write(f"{Color.RED}✘ FAIL{Color.RESET} ")
        self.stream.writeln(f"{Color.CYAN}{test}{Color.RESET}")

    def addError(self, test, err):
        super().addError(test, err)
        self.stream.write(f"{Color.YELLOW}⚠ ERROR{Color.RESET} ")
        self.stream.writeln(f"{Color.CYAN}{test}{Color.RESET}")


class ColorTextTestRunner(unittest.TextTestRunner):
    resultclass = ColorTextTestResult


# ---------------------------------------------------------
# 4) CLI argumenty
# ---------------------------------------------------------
def parse_args():
    parser = argparse.ArgumentParser(description="Run unit tests with fake hardware.")
    parser.add_argument(
        "--pattern",
        default="test*.py",
        help="Pattern for test discovery (default: test*.py)"
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="count",
        default=1,
        help="Increase verbosity (use -vv for more)"
    )
    return parser.parse_args()


# ---------------------------------------------------------
# 5) Hlavní funkce
# ---------------------------------------------------------
def main():
    args = parse_args()

    print(f"{Color.CYAN}{Color.BOLD}Running tests...{Color.RESET}")

    test_dir = os.path.join(BASE_DIR, "tests")
    loader = unittest.TestLoader()
    suite = loader.discover(test_dir, pattern=args.pattern)

    runner = ColorTextTestRunner(verbosity=args.verbose)
    result = runner.run(suite)

    if result.wasSuccessful():
        print(f"\n{Color.GREEN}{Color.BOLD}ALL TESTS PASSED ✔{Color.RESET}")
    else:
        print(f"\n{Color.RED}{Color.BOLD}SOME TESTS FAILED ✘{Color.RESET}")

    sys.exit(not result.wasSuccessful())


if __name__ == "__main__":
    main()
