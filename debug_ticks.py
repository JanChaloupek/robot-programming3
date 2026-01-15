import sys
import os

BASE_DIR = os.path.dirname(__file__)
LIB_DIR = os.path.join(BASE_DIR, "lib_vsc_only")
sys.path.insert(0, LIB_DIR)

import lib_vsc_only.adafruit_ticks as t
print("LOADED FROM:", t.__file__)
print("HAS set_ticks_ms:", hasattr(t, "set_ticks_ms"))
print("DIR:", dir(t))
