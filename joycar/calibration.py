"""
calibration.py – Kalibrační koeficienty motorů pro robot JoyCar.

Tento modul vychází z měření a kalibrací v 1-SW_GIT a 2-SW_GIT.
Umožňuje převod požadované úhlové rychlosti kola (v rad/s) na PWM signál
podle naměřeného lineárního modelu:

    PWM = a * |omega| + b

Podporuje jak 8bitový budič PCA9633 (PWM -255 .. 255),
tak 12bitový náhradní budič PCA9685 (PWM -4095 .. 4095).
"""


class CalibrateFactors:
    """
    Uchovává kalibrační konstanty pro jeden motor kola.

    Parametry:
        minimumAngularSpeed (float): Minimální úhlová rychlost v rad/s.
        minPwm_WhenStopped (int): Minimální PWM potřebné k rozjezdu ze stoje (deadzone).
        minPwm_InMotion (int): Minimální PWM potřebné k udržení otáčení v chodu.
        a (float): Směrnice lineární závislosti (strmost).
        b (float): Posun lineární závislosti (klidový offset).
        maxPwm (int): Maximální povolená hodnota PWM (255 pro PCA9633, 4095 pro PCA9685).
    """

    def __init__(self,
                 minimumAngularSpeed: float = 0.0,
                 minPwm_WhenStopped: int = 20,
                 minPwm_InMotion: int = 15,
                 a: float = 17.0,
                 b: float = 28.0,
                 maxPwm: int = 255) -> None:
        self.minimumAngularSpeed = minimumAngularSpeed
        self.minPwm_WhenStopped = minPwm_WhenStopped
        self.minPwm_InMotion = minPwm_InMotion
        self.a = a
        self.b = b
        self.maxPwm = maxPwm

    def calculatePwm(self, angularSpeed: float) -> int:
        """
        Vypočte hodnotu PWM pro zadanou úhlovou rychlost v rad/s.

        Kladná hodnota = otáčení dopředu.
        Záporná hodnota = otáčení dozadu.
        Nula = stop (0).
        """
        if angularSpeed == 0.0:
            return 0

        raw_pwm = int(self.a * abs(angularSpeed) + self.b)
        pwm = min(self.maxPwm, max(0, raw_pwm))

        if angularSpeed < 0:
            pwm = -pwm
        return pwm

    def getMinimumPwm(self, isStopped: bool = True) -> int:
        """Vrátí minimální PWM potřebné pro rozjezd (True) nebo udržení pohybu (False)."""
        return self.minPwm_WhenStopped if isStopped else self.minPwm_InMotion

    @classmethod
    def forPCA9633(cls,
                   a: float = 17.0,
                   b: float = 28.0,
                   minStopped: int = 20,
                   minMotion: int = 15,
                   minSpeed: float = 0.0) -> "CalibrateFactors":
        """Vytvoří přednastavené kalibrační koeficienty pro 8bitový čip PCA9633 (0–255)."""
        return cls(minimumAngularSpeed=minSpeed,
                   minPwm_WhenStopped=minStopped,
                   minPwm_InMotion=minMotion,
                   a=a,
                   b=b,
                   maxPwm=255)

    @classmethod
    def forPCA9685(cls,
                   a: float = 272.0,
                   b: float = 448.0,
                   minStopped: int = 320,
                   minMotion: int = 240,
                   minSpeed: float = 0.0) -> "CalibrateFactors":
        """Vytvoří přednastavené kalibrační koeficienty pro 12bitový čip PCA9685 (0–4095)."""
        return cls(minimumAngularSpeed=minSpeed,
                   minPwm_WhenStopped=minStopped,
                   minPwm_InMotion=minMotion,
                   a=a,
                   b=b,
                   maxPwm=4095)

    def __repr__(self) -> str:
        return (f"CalibrateFactors(a={self.a}, b={self.b}, "
                f"minStopped={self.minPwm_WhenStopped}, minMotion={self.minPwm_InMotion}, "
                f"maxPwm={self.maxPwm})")
