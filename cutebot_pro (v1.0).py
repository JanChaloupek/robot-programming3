import time
import board
import busio

class CuteBotPro:
    def __init__(self, i2c: busio.I2C | None = None, addr: int = 0x10) -> None:
        self.addr = addr
        self.i2c = i2c or busio.I2C(board.SCL, board.SDA)
        self._four_way_state_value = 0
        self._time_delay = 500
        self._block_length = 0
        self._block_unit = 0  # 0 = cm, 1 = inch

    # -------------------------
    # Interní pomocné funkce
    # -------------------------
    def _send(self, command: int, params=()):
        frame = bytearray(4 + len(params))
        frame[0] = 0xFF
        frame[1] = 0xF9
        frame[2] = command
        frame[3] = len(params)
        for i, p in enumerate(params):
            frame[4 + i] = p & 0xFF

        while not self.i2c.try_lock():
            pass
        try:
            self.i2c.writeto(self.addr, frame)
        finally:
            self.i2c.unlock()

        time.sleep(0.001)

    def _read(self, nbytes: int) -> bytes:
        buf = bytearray(nbytes)

        while not self.i2c.try_lock():
            pass
        try:
            self.i2c.readfrom_into(self.addr, buf)
        finally:
            self.i2c.unlock()

        return bytes(buf)

    @staticmethod
    def _map(x: int | float, in_min: int, in_max: int, out_min: int, out_max: int) -> float:
        return (x - in_min) * (out_max - out_min) / (in_max - in_min) + out_min

    def set_pause_base(self, base_ms: int) -> None:
        self._time_delay = base_ms

    def _pid_pause(self, ms: int) -> None:
        end_time = time.monotonic() + ms / 1000.0
        while True:
            self._send(0xA0, [0x05])
            status = self._read(1)[0]
            if status != 0 or time.monotonic() >= end_time:
                time.sleep(0.5)
                break
            time.sleep(0.01)

    # -------------------------
    # Motor control
    # -------------------------
    def motor_control(self, wheel: int, left_speed: int, right_speed: int) -> None:
        direction = 0
        if left_speed < 0:
            direction |= 0x01
        if right_speed < 0:
            direction |= 0x02
        self._send(0x10, [wheel, abs(left_speed), abs(right_speed), direction])

    # -------------------------
    # Headlights (RGB)
    # -------------------------
    def color_light(self, light: int, color: int) -> None:
        r = (color >> 16) & 0xFF
        g = (color >> 8) & 0xFF
        b = color & 0xFF
        self._send(0x20, [light, abs(r), abs(g), abs(b)])

    def single_headlights(self, light: int, r: int, g: int, b: int) -> None:
        self._send(0x20, [light, abs(r), abs(g), abs(b)])

    def turn_off_all_headlights(self) -> None:
        self._send(0x20, [2, 0, 0, 0])

    # -------------------------
    # Extended motor
    # -------------------------
    def extend_motor_control(self, speed: int) -> None:
        direction = 0
        if speed > 0:
            direction |= 0x01
        self._send(0x30, [abs(speed), direction])

    def extend_motor_stop(self) -> None:
        self._send(0x30, [0, 0])

    # -------------------------
    # Servo
    # -------------------------
    def extend_servo_control(self, servotype: int, index: int, angle: int) -> None:
        if servotype == 1:
            angle_map = int(self._map(angle, 0, 180, 0, 180))
        elif servotype == 2:
            angle_map = int(self._map(angle, 0, 270, 0, 180))
        elif servotype == 3:
            angle_map = int(self._map(angle, 0, 360, 0, 180))
        else:
            angle_map = angle
        self._send(0x40, [index, angle_map])

    def continuous_servo_control(self, index: int, speed: int) -> None:
        speed_mapped = int(self._map(speed, -100, 100, 0, 180))
        self.extend_servo_control(1, index, speed_mapped)

    # -------------------------
    # Speed & distance (enkodéry)
    # -------------------------
    def read_speed(self, motor: int, speed_units: int = 0) -> float:
        self._send(0xA0, [motor + 1])
        buf = self._read(1)
        speed = buf[0]
        if speed_units == 0:
            return float(speed)
        return speed / 0.3937

    def read_distance(self, motor: int) -> int:
        self._send(0xA0, [motor + 3])
        buf = self._read(4)
        return int.from_bytes(buf, "little", signed=True)

    def clear_wheel_turn(self, motor: int) -> None:
        self._send(0x50, [motor])

    # -------------------------
    # 4-way line sensor
    # -------------------------
    def trackbit_state_value(self) -> None:
        self._send(0x60, [0x00])
        states = self._read(1)[0]
        self._four_way_state_value = states

    def get_offset(self) -> int:
        self._send(0x60, [0x01])
        buf = self._read(2)
        offset = (buf[0] << 8) | buf[1]
        offset = int(self._map(offset, 0, 6000, -3000, 3000))
        return offset

    def get_grayscale_sensor_state(self, state: int) -> bool:
        return self._four_way_state_value == state

    def trackbit_channel_state(self, channel: int, state: int) -> bool:
        mask = 1 << channel
        if state == 1:
            return (self._four_way_state_value & mask) != 0
        else:
            return (self._four_way_state_value & mask) == 0

    def trackbit_get_gray(self, channel: int) -> int:
        self._send(0x60, [0x02, channel])
        return self._read(1)[0]

    # -------------------------
    # PID control – speed
    # -------------------------
    def pid_speed_control(self, lspeed: int, rspeed: int, unit: int) -> None:
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

    # -------------------------
    # PID – distance
    # -------------------------
    def pid_run_distance(self, direction: int, distance: int, unit: int) -> None:
        distance *= (10 if unit == 0 else 25.4)
        temp_distance = distance
        d_h = (distance >> 8) & 0xFF
        d_l = distance & 0xFF
        direction_flag = 0 if direction == 0 else 3
        self._send(0x81, [d_h, d_l, direction_flag])
        self._pid_pause(round(temp_distance / 1000.0 * 8000 + 3000))

    def pid_speed_run_distance(self, speed: int, unitspeed: int, direction: int, distance: int, unit: int) -> None:
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

    # -------------------------
    # PID – angle
    # -------------------------
    def pid_run_angle(self, wheel: int, angle: int, angle_units: int) -> None:
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

    # -------------------------
    # PID – steering
    # -------------------------
    def pid_run_steering(self, turn: int, angle: int) -> None:
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

    # -------------------------
    # Block mode
    # -------------------------
    def pid_block_set(self, length: int, distance_unit: int) -> None:
        self._block_length = length
        self._block_unit = distance_unit

    def pid_run_block(self, cnt: int) -> None:
        self.pid_run_distance(0, self._block_length * cnt, self._block_unit)

    # -------------------------
    # Version
    # -------------------------
    def read_versions(self) -> str:
        self._send(0xA0, [0x00])
        buf = self._read(3)
        return f"V {buf[0]}.{buf[1]}.{buf[2]}"
