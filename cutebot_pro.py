import time
import board
import busio


class CuteBotPro:
    """
    Ovládání Cutebot Pro (verze 2 protokolu, rámec 0xFF 0xF9).

    - I2C adresa: default 0x10
    - Rámec: [0xFF, 0xF9, command, length, params...]
    - PID příkazy: 0x80–0x86
    """

    def __init__(self, i2c: busio.I2C | None = None, addr: int = 0x10) -> None:
        self.addr = addr
        self.i2c = i2c or busio.I2C(board.SCL, board.SDA)
        self._four_way_state_value = 0
        self._time_delay = 500  # základ pro čekání u PID (lze změnit set_pause_base)
        self._block_length = 0
        self._block_unit = 0  # 0 = cm, 1 = inch

    # -------------------------------------------------------------------------
    # Interní pomocné funkce
    # -------------------------------------------------------------------------
    def _send(self, command: int, params=()) -> None:
        """
        Odešle jeden I2C rámec ve formátu:
        [0xFF, 0xF9, command, len(params), params...]
        """
        frame = bytearray(4 + len(params))
        frame[0] = 0xFF
        frame[1] = 0xF9
        frame[2] = command & 0xFF
        frame[3] = len(params) & 0xFF
        for i, p in enumerate(params):
            frame[4 + i] = p & 0xFF

        while not self.i2c.try_lock():
            pass
        try:
            self.i2c.writeto(self.addr, frame)
        finally:
            self.i2c.unlock()

        # krátké zpoždění, aby firmware stihl rámec zpracovat
        time.sleep(0.001)

    def _read(self, nbytes: int) -> bytes:
        """
        Přečte nbytes z I2C zařízení.
        """
        buf = bytearray(nbytes)

        while not self.i2c.try_lock():
            pass
        try:
            self.i2c.readfrom_into(self.addr, buf)
        finally:
            self.i2c.unlock()

        return bytes(buf)

    @staticmethod
    def _map(x: float, in_min: float, in_max: float, out_min: float, out_max: float) -> float:
        """
        Lineární mapování hodnoty x z intervalu [in_min, in_max] do [out_min, out_max].
        """
        return (x - in_min) * (out_max - out_min) / (in_max - in_min) + out_min

    def set_pause_base(self, base_ms: int) -> None:
        """
        Nastaví základní časovou konstantu pro čekání v PID funkcích (není přímo ve fw,
        ale můžeš si podle toho upravit chování _pid_pause).
        """
        self._time_delay = base_ms

    def _pid_pause(self, ms: int) -> None:
        """
        Čeká, dokud:
        - firmware neoznámí dokončení PID akce (0xA0, [0x05] → status != 0), nebo
        - nevyprší timeout ms.

        Toto odpovídá logice pidPause() z V2 knihovny.
        """
        end_time = time.monotonic() + ms / 1000.0
        while True:
            self._send(0xA0, [0x05])
            status = self._read(1)[0]
            if status != 0 or time.monotonic() >= end_time:
                time.sleep(0.5)
                break
            time.sleep(0.01)

    # -------------------------------------------------------------------------
    # Motor control (přímé řízení motorů, bez PID)
    # -------------------------------------------------------------------------
    def motor_control(self, wheel: int, left_speed: int, right_speed: int) -> None:
        """
        Přímé řízení motorů (bez PID).

        wheel:
            0 = levé kolo
            1 = pravé kolo
            2 = obě kola

        left_speed, right_speed:
            -100 až 100 (znaménko = směr)
        """
        direction = 0
        if left_speed < 0:
            direction |= 0x01
        if right_speed < 0:
            direction |= 0x02
        self._send(0x10, [wheel, abs(left_speed), abs(right_speed), direction])

    # -------------------------------------------------------------------------
    # Headlights (RGB)
    # -------------------------------------------------------------------------
    def color_light(self, light: int, color: int) -> None:
        """
        Nastaví barvu světlometů.

        light:
            0 = levý
            1 = pravý
            2 = oba

        color:
            0xRRGGBB
        """
        r = (color >> 16) & 0xFF
        g = (color >> 8) & 0xFF
        b = color & 0xFF
        self._send(0x20, [light, abs(r), abs(g), abs(b)])

    def single_headlights(self, light: int, r: int, g: int, b: int) -> None:
        """
        Nastaví barvu světlometu explicitně přes R, G, B (0–255).
        """
        self._send(0x20, [light, abs(r), abs(g), abs(b)])

    def turn_off_all_headlights(self) -> None:
        """
        Zhasne oba světlomety.
        """
        self._send(0x20, [2, 0, 0, 0])

    # -------------------------------------------------------------------------
    # Extended motor (externí DC motor)
    # -------------------------------------------------------------------------
    def extend_motor_control(self, speed: int) -> None:
        """
        Řízení rozšiřujícího DC motoru.

        speed:
            -100 až 100 (znaménko = směr)
        """
        direction = 0
        if speed > 0:
            direction |= 0x01
        self._send(0x30, [abs(speed), direction])

    def extend_motor_stop(self) -> None:
        """
        Zastaví rozšiřující DC motor.
        """
        self._send(0x30, [0, 0])

    # -------------------------------------------------------------------------
    # Servo
    # -------------------------------------------------------------------------
    def extend_servo_control(self, servotype: int, index: int, angle: int) -> None:
        """
        Řízení serva.

        servotype:
            1 = 180°
            2 = 270°
            3 = 360° (mapováno na 0–180)

        index:
            0–3 (M1–M4)

        angle:
            úhel v příslušném rozsahu (podle servotype)
        """
        if servotype == 1:
            angle_map = int(self._map(angle, 0, 180, 0, 180))
        elif servotype == 2:
            angle_map = int(self._map(angle, 0, 270, 0, 180))
        elif servotype == 3:
            angle_map = int(self._map(angle, 0, 360, 0, 180))
        else:
            angle_map = angle & 0xFF
        self._send(0x40, [index, angle_map])

    def continuous_servo_control(self, index: int, speed: int) -> None:
        """
        Řízení kontinuálního serva (rychlost -100 až 100).
        """
        speed_mapped = int(self._map(speed, -100, 100, 0, 180))
        self.extend_servo_control(1, index, speed_mapped)

    # -------------------------------------------------------------------------
    # Speed & distance (enkodéry)
    # -------------------------------------------------------------------------
    def read_speed(self, motor: int, speed_units: int = 0) -> float:
        """
        Čte rychlost motoru.

        motor:
            0 = M1 (levý)
            1 = M2 (pravý)

        speed_units:
            0 = cm/s
            1 = inch/s
        """
        self._send(0xA0, [motor + 1])
        buf = self._read(1)
        speed = buf[0]
        if speed_units == 0:
            return float(speed)
        return speed / 0.3937

    def read_distance(self, motor: int) -> int:
        """
        Čte ujetou vzdálenost (enkodér) v interních jednotkách (Int32LE).

        motor:
            0 = M1
            1 = M2
        """
        self._send(0xA0, [motor + 3])
        buf = self._read(4)
        return int.from_bytes(buf, "little")

    def clear_wheel_turn(self, motor: int) -> None:
        """
        Vynuluje počítadlo otáček/enkodéru pro daný motor.

        motor:
            0 = M1
            1 = M2
        """
        self._send(0x50, [motor])

    # -------------------------------------------------------------------------
    # 4-way line sensor
    # -------------------------------------------------------------------------
    def trackbit_state_value(self) -> None:
        """
        Načte stav 4-kanálového line-followeru (bitové pole 0–15).
        """
        self._send(0x60, [0x00])
        states = self._read(1)[0]
        self._four_way_state_value = states

    def get_offset(self) -> int:
        """
        Vrátí offset čáry (mapovaný z 0–6000 na -3000 až 3000).
        """
        self._send(0x60, [0x01])
        buf = self._read(2)
        offset = (buf[0] << 8) | buf[1]
        offset = int(self._map(offset, 0, 6000, -3000, 3000))
        return offset

    def get_grayscale_sensor_state(self, state: int) -> bool:
        """
        Porovná aktuální stav line-followeru s danou hodnotou (0–15).
        """
        return self._four_way_state_value == state

    def trackbit_channel_state(self, channel: int, state: int) -> bool:
        """
        Zjistí stav konkrétního kanálu.

        channel:
            0–3

        state:
            0 = „prázdný“ (hollow)
            1 = „plný“ (solid)
        """
        mask = 1 << channel
        if state == 1:
            return (self._four_way_state_value & mask) != 0
        else:
            return (self._four_way_state_value & mask) == 0

    def trackbit_get_gray(self, channel: int) -> int:
        """
        Vrátí šedou hodnotu (0–255) pro daný kanál line-followeru.
        """
        self._send(0x60, [0x02, channel])
        return self._read(1)[0]

    # -------------------------------------------------------------------------
    # PID control – speed (0x80)
    # -------------------------------------------------------------------------
    def pid_speed_control(self, lspeed: int, rspeed: int, unit: int) -> None:
        """
        PID řízení rychlosti obou kol.

        lspeed, rspeed:
            rychlost v cm/s nebo inch/s (podle unit)
            fw si to interně mapuje na 200–500 (20–50 cm/s)

        unit:
            0 = cm/s
            1 = inch/s
        """
        direction = 0
        if lspeed < 0:
            direction |= 0x01
        if rspeed < 0:
            direction |= 0x02

        if unit == 0:
            lspeed *= 10
            rspeed *= 10
        elif unit == 1:
            lspeed *= 25.4
            rspeed *= 25.4

        if lspeed != 0:
            lspeed = abs(lspeed)
            lspeed = min(lspeed, 500)
            lspeed = max(lspeed, 200)

        if rspeed != 0:
            rspeed = abs(rspeed)
            rspeed = min(rspeed, 500)
            rspeed = max(rspeed, 200)

        ls_h = (lspeed >> 8) & 0xFF
        ls_l = lspeed & 0xFF
        rs_h = (rspeed >> 8) & 0xFF
        rs_l = rspeed & 0xFF

        self._send(0x80, [ls_h, ls_l, rs_h, rs_l, direction])

    # -------------------------------------------------------------------------
    # PID – distance (0x81, 0x84)
    # -------------------------------------------------------------------------
    def pid_run_distance(self, direction: int, distance: int, unit: int) -> None:
        """
        PID jízda na danou vzdálenost (bez explicitní rychlosti).

        direction:
            0 = vpřed
            1 = vzad

        distance:
            vzdálenost v cm nebo inch (podle unit)

        unit:
            0 = cm
            1 = inch
        """
        distance *= (10 if unit == 0 else 25.4)
        temp_distance = distance
        d_h = (distance >> 8) & 0xFF
        d_l = distance & 0xFF
        direction_flag = 0 if direction == 0 else 3
        self._send(0x81, [d_h, d_l, direction_flag])
        self._pid_pause(round(temp_distance / 1000.0 * 8000 + 3000))

    def pid_speed_run_distance(self, speed: int, unitspeed: int, direction: int, distance: int, unit: int) -> None:
        """
        PID jízda na danou vzdálenost s danou rychlostí.

        speed:
            20–50 cm/s (fw si to mapuje na 200–500)

        unitspeed:
            0 = cm/s
            1 = inch/s

        direction:
            0 = vpřed
            1 = vzad

        distance:
            vzdálenost v cm nebo inch

        unit:
            0 = cm
            1 = inch
        """
        distance *= (10 if unit == 0 else 25.4)
        temp_distance = distance
        d_h = (distance >> 8) & 0xFF
        d_l = distance & 0xFF
        direction_flag = 0 if direction == 0 else 3

        if unitspeed == 1:
            speed *= 25.4
        else:
            speed *= 10

        if speed <= 0:
            speed = 0
        else:
            speed = max(200, min(speed, 500))

        s_h = (speed >> 8) & 0xFF
        s_l = speed & 0xFF

        self._send(0x84, [d_h, d_l, s_h, s_l, direction_flag])
        self._pid_pause(round(temp_distance / 1000.0 * 8000 + 3000))

    # -------------------------------------------------------------------------
    # PID – angle (0x83, 0x86)
    # -------------------------------------------------------------------------
    def pid_run_angle(self, wheel: int, angle: int, angle_units: int) -> None:
        """
        PID otočení kola/koleček o daný úhel.

        wheel:
            0 = levé
            1 = pravé
            2 = obě

        angle:
            hodnota úhlu (podle angle_units)

        angle_units:
            0 = stupně
            1 = počet otáček (circle → *360)
        """
        l_h = l_l = r_h = r_l = 0
        direction = 0
        if angle_units == 1:
            angle *= 360
        if angle < 0:
            direction = 3
        temp_angle = angle
        angle *= 10

        if wheel == 0 or wheel == 2:
            l_l = angle & 0xFF
            l_h = (angle >> 8) & 0xFF
        if wheel == 1 or wheel == 2:
            r_l = angle & 0xFF
            r_h = (angle >> 8) & 0xFF

        self._send(0x83, [l_h, l_l, r_h, r_l, direction])
        self._pid_pause(round(temp_angle / 360.0 * 2000 + 3000))

    def pid_speed_run_angle(self, speed: int, wheel: int, angle: int, angle_units: int) -> None:
        """
        PID otočení kola/koleček o daný úhel s danou rychlostí.

        speed:
            1–100 (mapováno na 100–400 interně)

        wheel:
            0 = levé
            1 = pravé
            2 = obě

        angle, angle_units:
            stejně jako u pid_run_angle()
        """
        if speed == 0:
            return
        if speed >= 100:
            speed = 100
        speed = round(self._map(speed, 1, 100, 100, 400))
        s_h = (speed >> 8) & 0xFF
        s_l = speed & 0xFF

        l_h = l_l = r_h = r_l = 0
        direction = 0
        if angle_units == 1:
            angle *= 360
        if angle < 0:
            direction = 3
        temp_angle = angle
        angle *= 10

        if wheel == 0 or wheel == 2:
            l_l = angle & 0xFF
            l_h = (angle >> 8) & 0xFF
        if wheel == 1 or wheel == 2:
            r_l = angle & 0xFF
            r_h = (angle >> 8) & 0xFF

        self._send(0x86, [l_h, l_l, r_h, r_l, s_h, s_l, direction])
        self._pid_pause(round(temp_angle / 360.0 * 3000 + 3000))

    # -------------------------------------------------------------------------
    # PID – steering (0x82, 0x85)
    # -------------------------------------------------------------------------
    def pid_run_steering(self, turn: int, angle: int) -> None:
        """
        PID řízení zatáčení (steering).

        turn:
            0 = Left steering
            1 = Right steering
            2 = Left in place (otáčení na místě vlevo)
            3 = Right in place (otáčení na místě vpravo)

        angle:
            úhel (fw si ho interně násobí / interpretuje)
        """
        l_h = l_l = r_h = r_l = 0
        direction = 0
        temp_angle = angle

        if turn == 0:
            angle *= 2
            r_h = (angle >> 8) & 0xFF
            r_l = angle & 0xFF
        elif turn == 1:
            angle *= 2
            l_h = (angle >> 8) & 0xFF
            l_l = angle & 0xFF
        elif turn == 2:
            r_h = (angle >> 8) & 0xFF
            r_l = angle & 0xFF
            l_h = (angle >> 8) & 0xFF
            l_l = angle & 0xFF
            direction = 1
        elif turn == 3:
            r_h = (angle >> 8) & 0xFF
            r_l = angle & 0xFF
            l_h = (angle >> 8) & 0xFF
            l_l = angle & 0xFF
            direction = 2

        self._send(0x82, [l_h, l_l, r_h, r_l, direction])
        self._pid_pause(round(temp_angle / 360.0 * 8000 + 3000))

    def pid_speed_run_steering(self, speed: int, turn: int, angle: int) -> None:
        """
        PID řízení zatáčení (steering) s danou rychlostí.

        speed:
            1–100 (mapováno na 100–400)

        turn:
            stejně jako u pid_run_steering()

        angle:
            úhel
        """
        if speed == 0:
            return
        if speed >= 100:
            speed = 100
        speed = round(self._map(speed, 1, 100, 100, 400))
        s_h = (speed >> 8) & 0xFF
        s_l = speed & 0xFF

        l_h = l_l = r_h = r_l = 0
        direction = 0
        temp_angle = angle

        if turn == 0:
            angle *= 2
            r_h = (angle >> 8) & 0xFF
            r_l = angle & 0xFF
        elif turn == 1:
            angle *= 2
            l_h = (angle >> 8) & 0xFF
            l_l = angle & 0xFF
        elif turn == 2:
            r_h = (angle >> 8) & 0xFF
            r_l = angle & 0xFF
            l_h = (angle >> 8) & 0xFF
            l_l = angle & 0xFF
            direction = 1
        elif turn == 3:
            r_h = (angle >> 8) & 0xFF
            r_l = angle & 0xFF
            l_h = (angle >> 8) & 0xFF
            l_l = angle & 0xFF
            direction = 2

        self._send(0x85, [l_h, l_l, r_h, r_l, s_h, s_l, direction])
        self._pid_pause(round(temp_angle / 360.0 * 8000 + 3000))

    # -------------------------------------------------------------------------
    # Block mode
    # -------------------------------------------------------------------------
    def pid_block_set(self, length: int, distance_unit: int) -> None:
        """
        Nastaví délku jednoho „bloku“ pro blokové řízení.

        length:
            délka bloku (v jednotkách distance_unit)

        distance_unit:
            0 = cm
            1 = inch
        """
        self._block_length = length
        self._block_unit = distance_unit

    def pid_run_block(self, cnt: int) -> None:
        """
        Ujede daný počet bloků (cnt * block_length).
        """
        self.pid_run_distance(0, self._block_length * cnt, self._block_unit)

    # -------------------------------------------------------------------------
    # Version
    # -------------------------------------------------------------------------
    def read_versions(self) -> str:
        """
        Přečte verzi firmware Cutebot Pro.

        Vrací:
            "V X.Y.Z"
        """
        self._send(0xA0, [0x00])
        buf = self._read(3)
        return f"V {buf[0]}.{buf[1]}.{buf[2]}"
