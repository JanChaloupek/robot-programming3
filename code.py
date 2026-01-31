from picoed import led
from joycar.display import display
from time import sleep, monotonic_ns

led.deinit()
led._init()

led.toggle()
display.iconA("A", flush=False)
startA = monotonic_ns()
display.iconB("B", flush=False)
endA = monotonic_ns()
print(f"Icon B drawing took {(endA - startA)/1000000} milliseconds")
display.iconC("C", flush=False)
startRedraw = monotonic_ns()
display.redraw()
endRedraw = monotonic_ns()
print(f"Redraw took {(endRedraw - startRedraw)/1000000} milliseconds")

sleep(1)
led.toggle()

display.fill(1)
sleep(0.5)
led.toggle()

startPixel = monotonic_ns()
display.pixel(0,0,255)
display.pixel(16,6,255)
startRedraw = monotonic_ns()
display.redraw()
endRedraw = monotonic_ns()

print(f"Pixel drawing took {(endRedraw - startPixel)/1000000} milliseconds")
print(f"Redraw took {(endRedraw - startRedraw)/1000000} milliseconds")
led.toggle()

display.fill(0)

