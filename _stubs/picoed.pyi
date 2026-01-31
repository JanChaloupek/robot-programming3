"""
Stub rozhraní pro CircuitPython modul `picoed`.

Obsahuje třídy a funkce dostupné při `import picoed`.
"""

class Image:
    NO: bytes
    SQUARE: bytes
    RECTANGLE: bytes
    RHOMBUS: bytes
    TARGET: bytes
    CHESSBOARD: bytes
    HAPPY: bytes
    SAD: bytes
    YES: bytes
    HEART: bytes
    TRIANGLE: bytes
    CHAGRIN: bytes
    SMILING_FACE: bytes
    CRY: bytes
    DOWNCAST: bytes
    LOOK_RIGHT: bytes
    LOOK_LEFT: bytes
    TONGUE: bytes
    PEEK_RIGHT: bytes
    PEEK_LEFT: bytes
    TEAR_EYES: bytes
    PROUD: bytes
    SNEER_LEFT: bytes
    SNEER_RIGHT: bytes
    SUPERCILIOUS_LOOK: bytes
    EXCITED: bytes

    def __new__(cls, value: str | None = None): ...


class Display:
    width: int
    height: int

    @staticmethod
    def pixel_addr(x: int, y: int) -> int: ...
    def clear(self) -> None: ...
    def scroll(self, value, brightness: int = 30) -> None: ...
    def show(self, value, brightness: int = 30) -> None: ...


class Button:
    def __init__(self, pin): ...
    def is_pressed(self) -> bool: ...
    def was_pressed(self) -> bool: ...


class Led:
    def __init__(self, pin): ...
    def _init(self) -> None: ...
    def deinit(self) -> None: ...
    def on(self) -> None: ...
    def off(self) -> None: ...
    def toggle(self) -> None: ...


class Music:
    def __init__(self, pin): ...
    def play(self, melody, wait: bool = True, loop: bool = False) -> None: ...
    def pitch(self, frequency: int, duration: int | None = None) -> None: ...
    def tone(self, frequency: int, duration: int | None = None) -> None: ...
    def stop(self) -> None: ...
    def reset(self) -> None: ...


# Modulové instance
i2c: object
internal_i2c: object
display: Display
button_a: Button
button_b: Button
led: Led
music: Music
