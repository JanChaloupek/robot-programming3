import unittest
from joycar.i2c import I2C
from busio import I2C as FakeI2C


class TestI2C(unittest.TestCase):
    """
    Testy základní funkcionality třídy I2C.

    Ověřujeme, že:
        - scan() vrací seznam dostupných zařízení simulovaných FakeI2C
        - write() správně předá adresu a data do FakeI2C
        - formát zápisu odpovídá očekávané podobě (adresa, seznam bytů)

    Testy slouží jako sanity‑check správné komunikace mezi I2C wrapperem
    a simulovaným hardwarem.
    """

    def test_scan(self):
        """
        Ověříme, že scan() vrátí seznam zařízení,
        která FakeI2C simuluje: [0x38, 0x62].
        """
        hw = FakeI2C()
        i2c = I2C(hw)
        self.assertEqual(i2c.scan(), [0x38, 0x62])

    def test_write(self):
        """
        Ověříme, že write() správně zapíše data na I2C sběrnici
        ve formátu (adresa, [data...]).
        """
        hw = FakeI2C()
        i2c = I2C(hw)

        i2c.write(0x10, bytes([0x01, 0x02]))

        self.assertEqual(hw.write_history[-1], (0x10, bytes([0x01, 0x02])))