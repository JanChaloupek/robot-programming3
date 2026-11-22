"""
test_code_simulation.py – Test simulace hlavního programu code.py / code_joycar.py.

Výukový modul pro studenty:
Ověřuje, že hlavní program robota proběhne bez chyb od inicializace,
přes běh superloopu, až po bezpečné zastavení tlačítkem A nebo nouzový shutdown.
"""

import unittest
import picoed
import code_joycar


class TestCodeSimulation(unittest.TestCase):
    """Testovací sada pro běh hlavního programu robota JoyCar."""

    def test_main_loop_and_clean_stop(self):
        """
        Ověří normální průběh:
        - inicializace baterie a robota
        - několik cyklů superloopu
        - stisk tlačítka A -> bezpečné zastavení robot.stop()
        """
        original_was_pressed = picoed.button_a.was_pressed
        press_sequence = [False, False, False, True]

        def fake_was_pressed():
            if press_sequence:
                return press_sequence.pop(0)
            return True

        try:
            picoed.button_a.was_pressed = fake_was_pressed
            code_joycar.main()
        finally:
            picoed.button_a.was_pressed = original_was_pressed

    def test_main_emergency_shutdown_on_exception(self):
        """
        Ověří, že při neočekávané chybě v superloopu
        se spolehlivě zavolá emergencyShutdown().
        """
        original_was_pressed = picoed.button_a.was_pressed

        def fake_raise():
            raise RuntimeError("Simulovaná HW chyba")

        try:
            picoed.button_a.was_pressed = fake_raise
            with self.assertRaises(RuntimeError):
                code_joycar.main()
        finally:
            picoed.button_a.was_pressed = original_was_pressed


if __name__ == "__main__":
    unittest.main()
