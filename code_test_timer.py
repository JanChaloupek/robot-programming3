import time
from utils import Timer, Period

print("Test Timer & Period start")

# Timer: jednorázový timeout 2 sekundy
t = Timer(timeout_ms=2000)

# Period: tiká každých 500 ms
p = Period(timeout_ms=500)

while True:
    # Test Timer
    if t.ready():
        print("Timer: timeout po 2 sekundách")
        t.stopTimer()

    # Test Period
    if p.ready():
        print("Period: tik")

    time.sleep(0.05)
