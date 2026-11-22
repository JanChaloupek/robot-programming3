"""
test_sound.py – Unit testy pro zvukový subsystém robota JoyCar.

Výukový modul pro studenty:
Ověřuje neblokující generování tónů pomocí PWM a časovače Period
bez použití reálného hardwaru bzučáku.
"""

import unittest
import board
import pwmio
import _fake.adafruit_ticks as fake_ticks
from busio import I2C as FakeI2C
from tests.create import createRobot
from joycar.sound import (
    HonkData,
    HornController,
    tutu,
    hello,
    brzdeni,
    panic,
)


class TestSound(unittest.TestCase):
    """Testovací sada pro datovou třídu HonkData a kontrolér HornController."""

    def setUp(self):
        fake_ticks.set_ticks_ms(0)

    def test_honk_data_validation(self):
        """Ověří správnou validaci vstupů v HonkData."""
        # Platná data
        data = HonkData(tones=[440, 880], durations=[100, 200], pauses=[50, 50])
        self.assertEqual(len(data), 2)
        self.assertEqual(data.tones, [440, 880])
        self.assertEqual(data.durations, [100, 200])
        self.assertEqual(data.pauses, [50, 50])

        # Prázdné seznamy musí vyvolat ValueError
        with self.assertRaises(ValueError):
            HonkData(tones=[], durations=[], pauses=[])

        # Neshodné délky seznamů musí vyvolat ValueError
        with self.assertRaises(ValueError):
            HonkData(tones=[440], durations=[100, 200], pauses=[50])

    def test_horn_controller_nonblocking_sequence(self):
        """
        Ověří, že přehrávání sekvence tónů probíhá neblokujícím způsobem:
        tón 1 (500 ms) -> pauza 1 (50 ms) -> tón 2 (700 ms) -> pauza 2 (1 ms) -> konec.
        """
        pwm = pwmio.PWMOut(board.BUZZER, frequency=1000, duty_cycle=0)
        horn = HornController(pwm_out=pwm)

        self.assertFalse(horn.is_playing)
        self.assertEqual(pwm.duty_cycle, 0)

        # 1. Spuštění melodie tutu: tones=[1000, 1000], durations=[500, 700], pauses=[50, 1]
        horn.play(tutu)

        self.assertTrue(horn.is_playing)
        self.assertTrue(horn.is_honking)
        self.assertEqual(pwm.frequency, 1000)
        self.assertEqual(pwm.duty_cycle, HornController.VOLUME_DUTY_CYCLE)

        # 2. Během tónu (čas 200 ms) – tón stále hraje
        fake_ticks.advance_ticks(200)
        horn.update()
        self.assertTrue(horn.is_playing)
        self.assertTrue(horn.is_honking)
        self.assertEqual(pwm.duty_cycle, HornController.VOLUME_DUTY_CYCLE)

        # 3. Vypršení prvního tónu (501 ms od začátku) – přechod do pauzy 1
        fake_ticks.advance_ticks(301)
        horn.update()
        self.assertTrue(horn.is_playing)
        self.assertFalse(horn.is_honking, "Po vypršení tónu musí nastat pauza (ticho)")
        self.assertEqual(pwm.duty_cycle, 0, "Během pauzy musí být střída PWM 0")

        # 4. Vypršení pauzy 1 (pauza trvá 50 ms -> posun o 55 ms) – začátek tónu 2
        fake_ticks.advance_ticks(55)
        horn.update()
        self.assertTrue(horn.is_playing)
        self.assertTrue(horn.is_honking)
        self.assertEqual(pwm.frequency, 1000)
        self.assertEqual(pwm.duty_cycle, HornController.VOLUME_DUTY_CYCLE)

        # 5. Vypršení tónu 2 (tón 2 trvá 700 ms -> posun o 705 ms) – přechod do pauzy 2
        fake_ticks.advance_ticks(705)
        horn.update()
        self.assertTrue(horn.is_playing)
        self.assertFalse(horn.is_honking)
        self.assertEqual(pwm.duty_cycle, 0)

        # 6. Vypršení pauzy 2 (trvá 1 ms -> posun o 5 ms) – ukončení melodie
        fake_ticks.advance_ticks(5)
        horn.update()
        self.assertFalse(horn.is_playing, "Po dohrání všech tónů musí být is_playing False")
        self.assertEqual(pwm.duty_cycle, 0)

    def test_horn_controller_stop(self):
        """Ověří okamžité ztišení a zastavení pomocí stop()."""
        pwm = pwmio.PWMOut(board.BUZZER, frequency=1000, duty_cycle=0)
        horn = HornController(pwm_out=pwm)

        horn.play(panic)
        self.assertTrue(horn.is_playing)
        self.assertEqual(pwm.duty_cycle, HornController.VOLUME_DUTY_CYCLE)

        # Zastavení
        horn.stop()
        self.assertFalse(horn.is_playing)
        self.assertFalse(horn.is_honking)
        self.assertEqual(pwm.duty_cycle, 0)

    def test_robot_sound_integration(self):
        """Ověří propojení zvukového subsystému s třídou JoyCarRobot."""
        hw = FakeI2C()
        robot = createRobot(hw)

        self.assertIsNotNone(robot.horn, "Robot musí mít inicializovaný atribut horn")

        # Spuštění znělky přes fasádní metodu robota
        robot.playHonk(hello)
        self.assertTrue(robot.horn.is_playing)

        # Update robota v superloopu automaticky aktualizuje i bzučák
        robot.update()
        self.assertTrue(robot.horn.is_playing)

        # Nouzové zastavení ztiší i bzučák
        robot.emergencyShutdown()
        self.assertFalse(robot.horn.is_playing)


if __name__ == "__main__":
    unittest.main()
