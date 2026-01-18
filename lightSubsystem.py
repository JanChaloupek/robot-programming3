from board import P0
from neopixel import NeoPixel
from code import DirectionEnum, Timer, Period
from velocity import Velocity

class BeamsEnum:
    DippedBeams = 1
    HighBeams = 2

class Indicator:
    # Třída implementující blinkr robota (nevykresluje, jen počítá stav)
    def __init__(self) -> None:
        self.direction = None
        self.warning = False
        self._indicatorPeriod = Period(timeout_ms=400)
        self.indicatorLight = None

    def update(self) -> None:           
        # aktualizuj stav blinkru
        if self.isLeft() or self.isRight():                        # blinker má být zapnutý 
            if self.indicatorLight is None:                        # ale nebliká
                self.indicatorLight = True                         # tak zační blikat
                self._indicatorPeriod.startTimer()
        else:                                                      # pokud má být vypnutý blinkr
            self.indicatorLight = None                             # vypni blinkr

        if self.indicatorLight is not None:                        # pokud blinkr bliká
            if self._indicatorPeriod.isTime():                    # a uplynul čas
                self.indicatorLight = not self.indicatorLight      # tak přepni stav
            
    def isLeft(self) -> bool:
        # je zapnutý levý blinkr?
        return (self.direction == DirectionEnum.LEFT)or self.warning

    def isRight(self) -> bool:
        # je zapnutý pravý blinkr?
        return (self.direction == DirectionEnum.RIGHT)or self.warning    

class LightsControl:
    # Třída ovládající světla robota (používá knihovnu NeoPixel)
    color_led_off = (0, 0, 0)
    color_led_orange = (100, 35, 0)
    color_led_white = (60, 60, 60)
    color_led_white_hi = (255, 255, 255)
    color_led_red = (60, 0, 0)
    color_led_red_br = (255, 0, 0)

    # (blinkry, zpátečku, brzdy, potkávací a dálková světla)
    ind_all = (1, 2, 4, 7)
    ind_left = (1, 4)
    ind_right = (2, 7)
    head_lights = (0, 3)
    back_lights = (5, 6)
    inside_light = (0, 3, 5, 6)
    reverse_lights = (5,)

    def __init__(self, velocity:Velocity) -> None:
        self.main = None
        self.indicator = Indicator()
        self._showPeriod = Period(timeout_ms=100)
        self._neopixels = NeoPixel(P0, 8)
        self._oldForward = 0.0
        self._velocity = velocity
        self._oldForward = 0.0
        self._brakeTimer = Timer(timeout_ms=600, startTimer=False)

    def _setBrakeFromVelocity(self) -> None:
        # spočti brzdové světlo z požadované dopředné rychlosti robota
        if self._velocity.forward == 0.0 and self._oldForward != 0.0:
            # pokud stojime ale predtim jsme jeli => brzdime
            self._brakeTimer.startTimer()
        self._oldForward = self._velocity.forward

    def _isBrake(self) -> bool:
        # má svítit brzdové světlo?
        if self._brakeTimer.isStarted():
            if not self._brakeTimer.isTimeout(timeout_ms=600):
                return True
            self._brakeTimer.stopTimer()
        return False

    def _isReverse(self) -> bool:
        return self._velocity.forward < 0.0

    def _setColorIndicator(self) -> None:
        # nastav stavy blinkrovych svetel
        leftColor = LightsControl.color_led_off
        rightColor = LightsControl.color_led_off
        if self.indicator.indicatorLight == True:
            if self.indicator.isLeft():
                leftColor = LightsControl.color_led_orange
            if self.indicator.isRight():
                rightColor = LightsControl.color_led_orange
        self._setColor(self.ind_left,  leftColor)
        self._setColor(self.ind_right, rightColor)

    def _setColorOtherLights(self) -> None:
        # nastav barvy prednich a zadnich svetel (ne blinkru)
        headColor = LightsControl.color_led_off
        backColor = LightsControl.color_led_off
        if self.main == BeamsEnum.DippedBeams:
            headColor = LightsControl.color_led_white
            backColor = LightsControl.color_led_red
        if self.main == BeamsEnum.HighBeams:
            headColor = LightsControl.color_led_white_hi
            backColor = LightsControl.color_led_red

        if self._isBrake():
            backColor = LightsControl.color_led_red_br

        self._setColor(self.head_lights, headColor)
        self._setColor(self.back_lights, backColor)
        
        if self._isReverse():
            self._setColor(self.reverse_lights, LightsControl.color_led_white)

    def update(self) -> None:
        self.indicator.update()
        if self._showPeriod.isTime():
            self._setBrakeFromVelocity()
            self._showColor()

    def _showColor(self) -> None:
        self._setColorIndicator()             # nastav barvy blinkrů
        self._setColorOtherLights()           # nastav barvy ostatních světel
        self._neopixels.write()               # zapiš nastavené barvy do led-ek

    def _setColorToOneLed(self, ledNo:int, color:list[int]) -> None:
        # nastav barvu pro jednu led-ku
        self._neopixels[ledNo] = color

    def _setColor(self, ledList:list[int], color:list[int]) -> None:
        # nastav barvu pro seznam led-ek
        for ledNo in ledList:
            self._setColorToOneLed(ledNo, color)
