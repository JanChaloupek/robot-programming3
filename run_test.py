import sys
import os
import unittest

# ---------------------------------------------------------
# 0) Přidat lib_vsc_only do sys.path
# ---------------------------------------------------------
BASE_DIR = os.path.dirname(__file__)
LIB_DIR = os.path.join(BASE_DIR, "lib_vsc_only")
sys.path.insert(0, LIB_DIR)

# ---------------------------------------------------------
# 1) Přesměrování adafruit_ticks → naše deterministická verze
#    (umístěná v lib_vsc_only/adafruit_ticks.py)
# ---------------------------------------------------------
import lib_vsc_only.adafruit_ticks as fake_ticks
sys.modules["adafruit_ticks"] = fake_ticks


# ---------------------------------------------------------
# 2) Přesměrování picoed → lib_vsc_only.picoed
# ---------------------------------------------------------
import lib_vsc_only.picoed as picoed_stub
sys.modules["picoed"] = picoed_stub


# ---------------------------------------------------------
# 3) Přesměrování time → fake_time
# ---------------------------------------------------------
import tests.fake_time as fake_time
sys.modules["time"] = fake_time


# ---------------------------------------------------------
# 4) Přesměrování board, neopixel, busio
# ---------------------------------------------------------

# Fake board
sys.modules["board"] = type("board", (), {"P0": 0})

# Fake neopixel
sys.modules["neopixel"] = type("neopixel", (), {
    "NeoPixel": lambda *args, **kwargs: None
})

# Fake busio
class FakeBusIO_I2C:
    def __init__(self, *args, **kwargs):
        pass

sys.modules["busio"] = type("busio", (), {
    "I2C": FakeBusIO_I2C
})


# ---------------------------------------------------------
# 4) Barevný výstup
# ---------------------------------------------------------
class Color:
    RESET = "\033[0m"
    BOLD = "\033[1m"
    GREEN = "\033[92m"
    RED = "\033[91m"
    YELLOW = "\033[93m"
    CYAN = "\033[96m"


class ColorTextTestResult(unittest.TextTestResult):
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
    resultclass = ColorTextTestResult


# ---------------------------------------------------------
# 5) Hlavní funkce
# ---------------------------------------------------------
def main():
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
