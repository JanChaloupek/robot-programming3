"""
test_pca9685.py – Unit testy pro budič PCA9685 a jeho třídu registrů PCA9685_registers.
"""

import unittest
from joycar import PCA9685, PCA9685_registers, I2C
from busio import I2C as FakeI2C


class TestPCA9685(unittest.TestCase):
    """Testuje správnou funkčnost PCA9685 a adresy v PCA9685_registers."""

    def test_registers_defined(self):
        """Ověří, že třída PCA9685_registers obsahuje všechny klíčové konstanty."""
        self.assertEqual(PCA9685_registers.MODE1, 0x00)
        self.assertEqual(PCA9685_registers.MODE1_VALUE, 0x20)
        self.assertEqual(PCA9685_registers.MODE2, 0x01)
        self.assertEqual(PCA9685_registers.PWM00, 0x06)
        self.assertEqual(PCA9685_registers.LED0_ON_L, 0x06)
        self.assertEqual(PCA9685_registers.PRE_SCALE, 0xFE)

    def test_init_motor_driver(self):
        """Ověří, že initMotorDriver probudí oscilátor zápisem MODE1_VALUE do MODE1."""
        hw = FakeI2C()
        pca = PCA9685(I2C(hw), address=0x61)
        pca.initMotorDriver()

        # Očekáváme zápis registru 0x00 s hodnotou 0x20 na adresu 0x61
        self.assertEqual(hw.write_history[-1], (0x61, bytes([0x00, 0x20])))

    def test_write_pwm_forward(self):
        """Ověří zápis dopředného PWM (kladná hodnota) na kanál 0 a 1."""
        hw = FakeI2C()
        pca = PCA9685(I2C(hw), address=0x61)

        # Dopředný výkon 2048 (polovina z 4095) na pravý motor (kanál 0)
        pca.writePwmToHbridge(0, 2048)

        # Poslední zápis na adresu 0x61:
        # byte 0: reg (0*4 + 0x06 = 0x06)
        # kanál 0: on=0, off=2048 (0x0800) -> 0, 0, 0x00, 0x08
        # kanál 1: on=0, off=4096 (0x1000) -> 0, 0, 0x00, 0x10
        addr, data = hw.write_history[-1]
        self.assertEqual(addr, 0x61)
        self.assertEqual(data[0], PCA9685_registers.PWM00)
        self.assertEqual(data[1:5], bytes([0x00, 0x00, 0x00, 0x08]))  # On=0, Off=2048
        self.assertEqual(data[5:9], bytes([0x00, 0x00, 0x00, 0x10]))  # On=0, Off=4096 (vypnuto)

    def test_write_pwm_reverse(self):
        """Ověří zápis zpětného PWM (záporná hodnota) na kanál 2 a 3."""
        hw = FakeI2C()
        pca = PCA9685(I2C(hw), address=0x61)

        # Zpětný výkon -1000 na levý motor (kanál 2)
        pca.writePwmToHbridge(2, -1000)

        addr, data = hw.write_history[-1]
        self.assertEqual(addr, 0x61)
        # kanál 2 začíná na 2*4 + 6 = 14 (0x0E)
        self.assertEqual(data[0], 2 * 4 + PCA9685_registers.PWM00)
        # kanál 2 (dopředu): vypnut (off=4096)
        self.assertEqual(data[1:5], bytes([0x00, 0x00, 0x00, 0x10]))
        # kanál 3 (dozadu): zapnut na 1000 (0x03E8)
        self.assertEqual(data[5:9], bytes([0x00, 0x00, 0xE8, 0x03]))


if __name__ == "__main__":
    unittest.main()
