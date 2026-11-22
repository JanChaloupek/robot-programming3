"""
line_trackers.py – Strategie vyhodnocování čáry pro 2 až 6 senzorů robota JoyCar.

Tento modul poskytuje názorné a snadno pochopitelné třídy pro různé hardwarové
konfigurace senzorů čáry na robotovi:
- LineTracker2: 2 senzory (jednoduchý základní robot: levý a pravý senzor).
- LineTracker3: 3 senzory (tovární JoyCar: levý, střední a pravý senzor).
- LineTracker4: 4 senzory (2 středové + 2 vnější senzory pro jemnější vedení).
- LineTracker5: 5 senzorů (3 středové + 2 předsazené krajní senzory pro křižovatky).
- LineTracker6: 6 senzorů (plná výbava z 2-SW_GIT s 9 detekčními zónami).

Každá třída je samostatná, přehledná a student v ní okamžitě vidí, jak daný hardware funguje.
"""

from typing import Optional, Any


class CrossRoadType:
    """Klasifikace typu detekované křižovatky."""
    NONE = 0
    LEFT = 1
    RIGHT = 2
    CROSS = 3


class BaseLineTracker:
    """Společný základ pro všechny konfigurace senzorů čáry."""

    sensorCount: int = 3
    xorMask: int = 0x1C

    def getLineDirection(self, s: Any) -> Optional[int]:
        """Vrátí směrovou odchylku od středu čáry (záporné = vpravo, kladné = vlevo, 0 = střed, None = ztráta)."""
        raise NotImplementedError

    def getTypeCrossRoads(self, s: Any) -> int:
        """Vrátí typ křižovatky (CrossRoadType.NONE, LEFT, RIGHT, CROSS)."""
        raise NotImplementedError

    def isCrossRoads(self, s: Any) -> bool:
        """Vrací True, pokud je detekována libovolná křižovatka."""
        return self.getTypeCrossRoads(s) != CrossRoadType.NONE


# =============================================================================
# 1. Dva senzory čáry (LineTracker2)
# =============================================================================
class LineTracker2(BaseLineTracker):
    """
    Řízení pomocí 2 senzorů (levý a pravý na spodku podvozku).

    Typické použití:
    - Čára vede mezi senzory (oba na bílém podkladu) = jedeme rovně (0).
    - Černá pod levým senzorem = zatoč vlevo (+2).
    - Černá pod pravým senzorem = zatoč vpravo (-2).
    - Oba senzory na černé = příčná stop čára / křižovatka (CROSS).
    """

    sensorCount = 2
    xorMask = 0x14  # Invertujeme bity 2 a 4 (0x04 | 0x10)

    def getLineDirection(self, s: Any) -> Optional[int]:
        left = s.areActive(s.LineLeft)
        right = s.areActive(s.LineRight)

        if left and right:
            return None  # Příčná čára / křižovatka
        elif left:
            return 2   # Čára ujíždí doleva -> stočit vlevo
        elif right:
            return -2  # Čára ujíždí doprava -> stočit vpravo
        else:
            return 0   # Čára je uprostřed mezi senzory

    def getTypeCrossRoads(self, s: Any) -> int:
        left = s.areActive(s.LineLeft)
        right = s.areActive(s.LineRight)
        if left and right:
            return CrossRoadType.CROSS
        return CrossRoadType.NONE


# =============================================================================
# 2. Tři senzory čáry (LineTracker3) – Tovární JoyCar
# =============================================================================
class LineTracker3(BaseLineTracker):
    """
    Standardní tovární výbava JoyCaru (3 senzory):
    - LineLeft (0x04), LineMiddle (0x08), LineRight (0x10).

    Směrová odchylka:
    -  None : Mimo čáru nebo křižovatka
    -     0 : Středový senzor na čáře (jedeme rovně)
    -    +1 : Středový + levý (mírně vlevo)
    -    +3 : Pouze levý (více vlevo)
    -    -1 : Středový + pravý (mírně vpravo)
    -    -3 : Pouze pravý (více vpravo)
    """

    sensorCount = 3
    xorMask = 0x1C  # 0x04 | 0x08 | 0x10

    def getLineDirection(self, s: Any) -> Optional[int]:
        left = s.areActive(s.LineLeft)
        right = s.areActive(s.LineRight)
        middle = s.areActive(s.LineMiddle)

        # Křižovatka
        if left and right:
            return None

        # Mimo čáru
        if not left and not right and not middle:
            return None

        # Přesně uprostřed
        if middle and not left and not right:
            return 0

        # Mírné odchylky
        if middle and left:
            return 1
        if middle and right:
            return -1

        # Výrazné odchylky
        if left:
            return 3
        if right:
            return -3

        return None

    def getTypeCrossRoads(self, s: Any) -> int:
        left = s.areActive(s.LineLeft)
        right = s.areActive(s.LineRight)
        middle = s.areActive(s.LineMiddle)

        if left and right:
            return CrossRoadType.CROSS
        if left and middle:
            return CrossRoadType.LEFT
        if right and middle:
            return CrossRoadType.RIGHT
        return CrossRoadType.NONE


# =============================================================================
# 3. Čtyři senzory čáry (LineTracker4)
# =============================================================================
class LineTracker4(BaseLineTracker):
    """
    Čtyři senzory čáry (2 vnitřní a 2 vnější):
    - LineLeft (0x04), LineMiddleLeft (0x08), LineMiddleRight (0x80), LineRight (0x10).
    """

    sensorCount = 4
    xorMask = 0x9C  # 0x04 | 0x08 | 0x10 | 0x80

    def getLineDirection(self, s: Any) -> Optional[int]:
        l = s.areActive(s.LineLeft)
        ml = s.areActive(s.LineMiddleLeft)
        mr = s.areActive(s.LineMiddleRight)
        r = s.areActive(s.LineRight)

        if l and r:
            return None
        if not l and not ml and not mr and not r:
            return None

        # Střed: oba vnitřní senzory vidí čáru
        if ml and mr:
            return 0
        # Mírné vyosení: jeden vnitřní senzor
        if ml and not mr and not l:
            return 1
        if mr and not ml and not r:
            return -1
        # Střední vyosení: vnitřní + vnější senzor
        if l and ml:
            return 2
        if r and mr:
            return -2
        # Větší vyosení: pouze vnější senzor
        if l and not ml:
            return 3
        if r and not mr:
            return -3

        return None

    def getTypeCrossRoads(self, s: Any) -> int:
        l = s.areActive(s.LineLeft)
        ml = s.areActive(s.LineMiddleLeft)
        mr = s.areActive(s.LineMiddleRight)
        r = s.areActive(s.LineRight)

        if l and r:
            return CrossRoadType.CROSS
        if l and ml:
            return CrossRoadType.LEFT
        if r and mr:
            return CrossRoadType.RIGHT
        return CrossRoadType.NONE


# =============================================================================
# 4. Pět senzorů čáry (LineTracker5)
# =============================================================================
class LineTracker5(BaseLineTracker):
    """
    Pět senzorů čáry:
    - 3 středové (LineLeft, LineMiddle, LineRight)
    - 2 předsazené krajní senzory (FarLeft 0x01, FarRight 0x02).
    """

    sensorCount = 5
    xorMask = 0x1F  # 0x01 | 0x02 | 0x04 | 0x08 | 0x10

    def getLineDirection(self, s: Any) -> Optional[int]:
        fl = s.areActive(s.LineFarLeft)
        l = s.areActive(s.LineLeft)
        m = s.areActive(s.LineMiddle)
        r = s.areActive(s.LineRight)
        fr = s.areActive(s.LineFarRight)

        if (l and r) or (fl and fr):
            return None
        if not fl and not l and not m and not r and not fr:
            return None

        # Krajní senzory mají nejvyšší prioritu pro vyosení
        if fl and not fr:
            return 5
        if fr and not fl:
            return -5

        # Vnitřní senzory
        if m and not l and not r:
            return 0
        if m and l and not r:
            return 1
        if l and not m and not r:
            return 3
        if m and r and not l:
            return -1
        if r and not m and not l:
            return -3

        return None

    def getTypeCrossRoads(self, s: Any) -> int:
        fl = s.areActive(s.LineFarLeft)
        l = s.areActive(s.LineLeft)
        r = s.areActive(s.LineRight)
        fr = s.areActive(s.LineFarRight)

        leftCross = fl or (l and fl)
        rightCross = fr or (r and fr)

        if leftCross and rightCross:
            return CrossRoadType.CROSS
        if leftCross:
            return CrossRoadType.LEFT
        if rightCross:
            return CrossRoadType.RIGHT
        if l and r:
            return CrossRoadType.CROSS
        return CrossRoadType.NONE


# =============================================================================
# 5. Šest senzorů čáry (LineTracker6) – Plná výbava z 2-SW_GIT
# =============================================================================
class LineTracker6(BaseLineTracker):
    """
    Šest senzorů čáry (architektura z 2-SW_GIT):
    - FarLeft (0x01), Left (0x04), MiddleLeft (0x08), MiddleRight (0x80), Right (0x10), FarRight (0x02).
    """

    sensorCount = 6
    xorMask = 0x9F  # 0x01 | 0x02 | 0x04 | 0x08 | 0x10 | 0x80

    def getLineDirection(self, s: Any) -> Optional[int]:
        fl = s.areActive(s.LineFarLeft)
        l = s.areActive(s.LineLeft)
        ml = s.areActive(s.LineMiddleLeft)
        mr = s.areActive(s.LineMiddleRight)
        r = s.areActive(s.LineRight)
        fr = s.areActive(s.LineFarRight)

        if (l and r) or (fl and fr):
            return None
        if not fl and not l and not ml and not mr and not r and not fr:
            return None

        # 1. Extrémní vyosení
        if fl and not fr:
            return 6
        if fr and not fl:
            return -6

        # 2. Vnitřní senzory
        if ml and mr:
            return 0
        if ml and not mr and not l:
            return 1
        if mr and not ml and not r:
            return -1
        if l and ml:
            return 2
        if r and mr:
            return -2
        if l and not ml:
            return 3
        if r and not mr:
            return -3

        return None

    def getTypeCrossRoads(self, s: Any) -> int:
        fl = s.areActive(s.LineFarLeft)
        l = s.areActive(s.LineLeft)
        r = s.areActive(s.LineRight)
        fr = s.areActive(s.LineFarRight)

        leftCross = (fl and l) or fl
        rightCross = (fr and r) or fr

        if leftCross and rightCross:
            return CrossRoadType.CROSS
        if leftCross:
            return CrossRoadType.LEFT
        if rightCross:
            return CrossRoadType.RIGHT
        if l and r:
            return CrossRoadType.CROSS
        return CrossRoadType.NONE


# =============================================================================
# Tovární funkce pro snadnou konfiguraci studentem
# =============================================================================
def createLineTracker(sensorCount: int = 3) -> BaseLineTracker:
    """
    Vytvoří příslušný sledovač čáry podle počtu osazených senzorů.

    Args:
        sensorCount (int): Počet senzorů (2, 3, 4, 5 nebo 6). Výchozí je 3.
    """
    trackers = {
        2: LineTracker2,
        3: LineTracker3,
        4: LineTracker4,
        5: LineTracker5,
        6: LineTracker6,
    }
    tracker_class = trackers.get(sensorCount)
    if tracker_class is None:
        raise ValueError(f"Nepodporovaný počet senzorů čáry: {sensorCount}. Podporovány jsou hodnoty 2 až 6.")
    return tracker_class()
