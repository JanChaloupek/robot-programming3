"""
Hybridní fake modul time.

- zachovává originální Python funkce (perf_counter, monotonic)
- poskytuje deterministické funkce pro studentský kód (time, sleep, sleep_ms, monotonic_ns)
"""

import time as _real_time
import adafruit_ticks as ticks

# Zachovat originální funkce pro unittest/coverage
perf_counter = _real_time.perf_counter
monotonic = _real_time.monotonic

# Fake funkce pro studentský kód
def monotonic_ns() -> int:
    """Deterministická verze monotonic_ns() pro studentský kód."""
    return ticks.ticks_ms() * 1_000_000

def time() -> float:
    """Deterministická verze time() pro studentský kód."""
    return ticks.ticks_ms() / 1000.0

def sleep(seconds: float) -> None:
    """Neblokující sleep pro studentský kód."""
    ticks.advance_ticks(int(seconds * 1000))

def sleep_ms(ms: int) -> None:
    """Neblokující sleep_ms pro studentský kód."""
    ticks.advance_ticks(int(ms))
