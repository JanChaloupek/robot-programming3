from joycar import display
from time import sleep, monotonic_ns

# robotLocalizeX = 5
# robotLocalizeY = 3
# separator = ":"
# text = str(robotLocalizeX) + separator + str(robotLocalizeY)
# start = monotonic_ns()
# display.scroll(text, brightness=8)
# end = monotonic_ns()
# print(f"scroll time: {(end - start) / 1_000_000:.2f} ms")

display.set_brightness(32)

print("Displaying position (8, 3)")
start = monotonic_ns()
display.position(8, 3)
end = monotonic_ns()
print(f"Time taken: {(end - start) / 1_000_000:.2f} ms")

print(f"Displaying character 'TL' in iconB")
start = monotonic_ns()
display.drive_mode("TL")
end = monotonic_ns()
print(f"Time taken: {(end - start) / 1_000_000:.2f} ms")

sleep(1.0)

print(f"Displaying number (123)")
start = monotonic_ns()
display.number(123)
end = monotonic_ns()
print(f"Time taken: {(end - start) / 1_000_000:.2f} ms")

sleep(1.0)

start = monotonic_ns()
display._bitmap(12, 0, 5, display._PICTOGRAMS["5"], 32)
end = monotonic_ns()
print(f"_bitmap time: {(end-start)/1_000_000}")

start = monotonic_ns()
display.iconA("5", flush=False)
end = monotonic_ns()
print(f"iconA time: {(end-start)/1_000_000}")

start = monotonic_ns()
display.flush()
end = monotonic_ns()
print(f"flush time: {(end-start)/1_000_000}")
