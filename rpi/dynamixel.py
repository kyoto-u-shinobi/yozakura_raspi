# (C) 2015  Kyoto University Mechatronics Laboratory
# Released under the GNU General Public License, version 3
import logging
import sys
import time

import serial

from common.exceptions import DynamixelError


class Dynamixel(object):
    class Response(object):
        def __init__(self, data):
            if not data or 0xff not in data[:2]:
                raise DynamixelError("Bad Header! ({data})".format(data=data))
            if Dynamixel._checksum(data[2:-1]) != data[-1]:
                raise DynamixelError("Checksum {chk} should be {good}!".format(
                    chk=Dynamixel._checksum(data[2:-1]), good=data[-1]))

            self.data = data
            self.response_id, self.length = data[2:4]
            self.errors = []
            for k in Dynamixel.errors.keys():
                if data[4] & k != 0:
                    self.errors.append(Dynamixel.errors[k])

            requested_data = self.data[5:-1]
            
            if not requested_data:
                return
            elif len(requested_data) == 1:
                self.value = requested_data[0]
            elif len(requested_data) == 2:
                self.value = (requested_data[1] << 8) + requested_data[0]
            else:
                raise DynamixelError("Bad number of values returned!")

        def __str__(self):
            return " ".join([hex(i) for i in self.data])

        def verify(self):
            if self.errors:
                raise DynamixelError("ERRORS: {e}".format(e=self.errors))
            return self

    _instructions = {"ping": 0x01,
                     "read_data": 0x02,
                     "write_data": 0x03,
                     "reg_write": 0x04,
                     "action": 0x05,
                     "reset": 0x06,
                     "sync_write": 0x83}

    _registers = {"model_number": 0x00,
                  "firmware_version": 0x02,
                  "id": 0x03,
                  "baudrate": 0x04,
                  "return_delay": 0x05,
                  "cw_limit": 0x06,
                  "ccw_limit": 0x08,
                  "max_temperature": 0x0B,
                  "min_voltage": 0x0C,
                  "max_voltage": 0x0D,
                  "max_torque": 0x0E,
                  "status_return_level": 0x10,
                  "alarm_led": 0x11,
                  "alarm_shutdown": 0x12,
                  "torque_enable": 0x18,
                  "led": 0x19,
                  "goal_position": 0x1E,
                  "moving_speed": 0x20,
                  "torque_limit": 0x22,
                  "present_position": 0x24,
                  "present_speed": 0x26,
                  "present_load": 0x28,
                  "present_voltage": 0x2A,
                  "present_temperature": 0x2B,
                  "registered_instruction": 0x2C,
                  "moving": 0x2E,
                  "lock": 0x2F,
                  "punch": 0x30}

    _register_minima = {}

    _register_maxima = {"id": 253,
                        "baudrate": 254,
                        "return_delay": 254,
                        "cw_limit": 1023,
                        "ccw_limit": 1023,
                        "max_temperature": 150,
                        "min_voltage": 250,
                        "max_voltage": 250,
                        "max_torque": 1023,
                        "status_return_level": 2,
                        "alarm_led": 127,
                        "alarm_shutdown": 127,
                        "torque_enable": 1,
                        "led": 1,
                        "goal_position": 1023,
                        "moving_speed": 1023,
                        "torque_limit": 1023,
                        "registered_instruction": 1,
                        "lock": 1,
                        "punch": 1023}

    _two_byte_registers = ["model_number",
                           "cw_limit", "ccw_limit", "max_torque",
                           "goal_position", "moving_speed", "torque_limit",
                           "present_position", "present_speed", "present_load",
                           "punch"]

    errors = {1:  "InputVoltage",
              2:  "AngleLimit",
              4:  "Overheating",
              8:  "Range",
              16: "Checksum",
              32: "Overload",
              64: "Instruction"}

    dx_ids = []

    def __init__(self, dx_id, dx_type="Dynamixel", name="Dynamixel",
                 port="/dev/ttyUSB0", baudrate=1000000, timeout=5):
        self._logger = logging.getLogger("{dx_type}-{name}".format(dx_type=dx_type, name=name))
        self._logger.debug("Initializing dynamixel")
        self._verify_id(dx_id)
        self.dx_type = dx_type
        self._dx_id = dx_id
        self.name = name
        self.port = port
        self.ser = serial.Serial(self.port, baudrate=baudrate, timeout=timeout)

        try:
            self.dx_id
        except DynamixelError:
            raise DynamixelError("ID# {dx_id} Dynamixel not connected.".format(
                dx_id=dx_id))

        Dynamixel.dx_ids.append(dx_id)
        self._logger.info("Dynamixel initialized")

    def _interact(self, packet):
        payload = [self._dx_id, len(packet)+1] + packet
        to_write = [0xFF, 0xFF] + payload + [Dynamixel._checksum(payload)]
        self.ser.write(bytes(to_write))
        time.sleep(0.05)

        res = self.ser.read(self.ser.inWaiting())
        response = Dynamixel.Response([i for i in res])

        return response.verify()
    
    def read(self, register):
        packet = []
        packet.append(self._instructions["read_data"])
        packet.append(self._registers[register])
        packet.append(self._register_length(register))
        return self._interact(packet).value

    def write(self, register, value):
        length = self._register_length(register)

        #if register == "goal_position" and self.multiturn_mode:
            #register_limit = "goal_position_multiturn"
        #else:
            #register_limit = register
#
        #if register_limit in self._register_minima:
            #min_value = self._register_minima[register_limit]
        #else:
            #min_value = 0
        #max_value = self._register_maxima[register_limit]
        #if not min_value <= value <= max_value:
            #raise DynamixelError("Illegal value: {v}".format(v=value))

        if value < 0:
            value += 2**16
        value = int(value)

        packet = []
        packet.append(self._instructions["write_data"])
        packet.append(self._registers[register])
        if length == 1:
            packet.append(value)
        else:
            packet.append(value & 255)
            packet.append(value >> 8)
        self._interact(packet)

    def reset(self):
        if 1 in Dynamixel.dx_ids and self.dx_id != 1:
            raise DynamixelError("Resetting would conflict with Dynamixel #1.")
        current_id = self.dx_id
        self._interact([self._instructions["reset"]])
        time.sleep(0.25)
        self._dx_id = 1
        self.dx_id = current_id

    @property
    def model_number(self):
        return self.read("model_number")

    @property
    def firmware_version(self):
        return self.read("firmware_version")

    @property
    def dx_id(self):
        return self.read("id")

    @dx_id.setter
    def dx_id(self, new_id):
        self._verify_id(new_id)
        old_id = self.dx_id
        self.write("id", new_id)
        self._dx_id = new_id
        Dynamixel.dx_ids.remove(old_id)
        Dynamixel.dx_ids.append(new_id)

    @property
    def baudrate(self):
        return 2000000 / (self.read("baudrate") + 1)

    @baudrate.setter
    def baudrate(self, baudrate):
        value = 2000000 / baudrate - 1
        self.write("baudrate", value)

    @property
    def return_delay(self):  # us
        return 2 * self.read("return_delay")

    @return_delay.setter
    def return_delay(self, value):
        self.write("return_delay", value / 2)

    @property
    def cw_limit_raw(self):
        return self.read("cw_limit")

    @cw_limit_raw.setter
    def cw_limit_raw(self, limit):
        self.write("cw_limit", limit)

    @property
    def cw_limit(self):
        alpha = self._max_turn_angle / self._register_maxima["cw_limit"]
        return self.cw_limit_raw * alpha

    @cw_limit.setter
    def cw_limit(self, deg):
        alpha = self._max_turn_angle / self._register_maxima["cw_limit"]
        self.cw_limit_raw = deg / alpha

    @property
    def ccw_limit_raw(self):
        return self.read("ccw_limit")

    @ccw_limit_raw.setter
    def ccw_limit_raw(self, limit):
        self.write("ccw_limit", limit)

    @property
    def ccw_limit(self):
        alpha = self._max_turn_angle / self._register_maxima["ccw_limit"]
        return self.ccw_limit_raw * alpha

    @ccw_limit.setter
    def ccw_limit(self, limit):
        alpha = self._max_turn_angle / self._register_maxima["ccw_limit"]
        self.ccw_limit_raw / alpha
    
    @property
    def limits(self):
        return self.cw_limit, self.ccw_limit

    @limits.setter
    def limits(self, limits):
        try:
            cw_limit = limits[0]
            ccw_limit = limits[1]
        except TypeError:
            cw_limit = ccw_limit = limits

        if cw_limit is not None:
            self.cw_limit = cw_limit
        if ccw_limit is not None:
            self.ccw_limit = ccw_limit

    @property
    def continuous_rotation(self):
        return self.cw_limit_raw == 0 and self.ccw_limit_raw == 0

    def engage_continuous_rotation(self):
        self.cw_limit_raw = 0
        self.ccw_limit_raw = 0

    @property
    def multiturn_mode(self):
        return self.cw_limit_raw == 4095 and self.ccw_limit_raw == 4095

    def engage_multiturn_mode(self):
        self.cw_limit_raw = 4095
        self.ccw_limit_raw = 4095

    @property
    def max_temperature(self):
        return self.read("max_temperature")
    
    @max_temperature.setter
    def max_temperature(self, value):
        self.write("max_temperature", value)

    @property
    def min_voltage(self):
        return self.read("min_voltage") / 10
    
    @min_voltage.setter
    def min_voltage(self, value):
        self.write("min_voltage", value * 10)

    @property
    def max_voltage(self):
        return self.read("max_voltage") / 10
    
    @max_voltage.setter
    def max_voltage(self, value):
        self.write("max_voltage", value * 10)

    @property
    def max_torque(self):
        return self.read("max_torque")
    
    @max_torque.setter
    def max_torque(self, value):
        self.write("max_torque", value)

    @property
    def status_return_level(self):
        return self.read("status_return_level")

    @status_return_level.setter
    def status_return_level(self, value):
        self.write("status_return_level", value)

    @property
    def alarm_led(self):
        return self.read("alarm_led")

    @alarm_led.setter
    def alarm_led(self, value):
        self.write("alarm_led", value)

    @property
    def alarm_shutdown(self):
        return self.read("alarm_shutdown")

    @alarm_shutdown.setter
    def alarm_shutdown(self, value):
        self.write("alarm_shutdown", value)

    @property
    def torque_enable(self):
        return self.read("torque_enable")

    @torque_enable.setter
    def torque_enable(self, value):
        self.write("torque_enable", value)

    @property
    def led(self):
        return self.read("led")

    @led.setter
    def led(self, value):
        self.write("led", value)

    @property
    def goal_raw(self):
        return self.read("goal_position")

    @goal_raw.setter
    def goal_raw(self, goal):
        self.write("goal_position", goal)

    @property
    def goal(self):
        alpha = self._max_turn_angle / self._register_maxima["goal_position"]
        pos = self.goal_raw
        if self.multiturn_mode and pos > self._register_maxima["goal_position_multiturn"]:
            pos -= 2**16
        return pos * alpha

    @goal.setter
    def goal(self, deg):
        alpha = self._max_turn_angle / self._register_maxima["goal_position"]
        self.goal_raw = deg / alpha

    @property
    def moving_speed(self):
        return self.read("moving_speed")

    @moving_speed.setter
    def moving_speed(self, speed):
        self.write("moving_speed", speed)

    @property
    def moving_speed_rpm(self):
        return self.moving_speed * 114 / 1023

    @moving_speed_rpm.setter
    def moving_speed_rpm(self, rpm):
        self.moving_speed = rpm * 1023 / 114
    
    @property
    def torque_limit(self):
        return self.read("torque_limit")

    @torque_limit.setter
    def torque_limit(self, torque_limit):
        self.write("torque_limit", torque_limit)

    @property
    def position_raw(self):
        return self.read("present_position")

    @property
    def position(self):
        alpha = self._max_turn_angle / self._register_maxima["goal_position"]
        pos = self.position_raw
        if self.multiturn_mode and pos > self._register_maxima["goal_position_multiturn"]:
            pos -= 2**16
        return pos * alpha

    @property
    def speed(self):
        return self.read("present_speed")

    @property
    def speed_rpm(self):
        speed = self.speed
        direction = speed >> 10
        return (speed & 1023) * 114 / 1023 * (1 if direction else -1)

    @property
    def load(self):
        load = self.read("present_load")
        direction = load >> 10
        return load * (1 if direction else -1)

    @property
    def voltage(self):
        return self.read("present_voltage") / 10

    @property
    def temperature(self):
        return self.read("present_temperature")

    @property
    def is_moving(self):
        """Return True if the servo is currently moving."""
        return self.read("moving")

    @property
    def lock(self):
        return self.read("lock")

    @lock.setter
    def lock(self, value):
        self.write("lock", value)

    @property
    def punch(self):
        return self.read("punch")

    @punch.setter
    def punch(self, value):
        self.write("punch", value)

    def wait_until_stopped(self):
        while self.is_moving:
            pass

    def _register_length(self, register):
        return 2 if register in self._two_byte_registers else 1

    def _verify_id(self, dx_id):
        if not 0 <= dx_id <= self._register_maxima["id"]:
            raise DynamixelError("ID {dx_id} is not legal!".format(dx_id=dx_id))

        if dx_id in Dynamixel.dx_ids:
            raise DynamixelError("ID# {dx_id} is already registered!".format(
                dx_id=dx_id))


    @staticmethod
    def _checksum(s):
        return (~sum(s)) & 0xFF

    def close(self):
        Dynamixel.dx_ids.remove(self.dx_id)
        self.ser.close()

    def __enter__(self):
        return self

    def __exit__(self, exit_type, value, traceback):
        self.close()

    def __del__(self):
        self.close()

    def __repr__(self):
        return "{dx_type} Dynamixel (ID# {dx_id}): {name}".format(
                dx_type=self.dx_type, dx_id=self.dx_id, name=self.name)

    def __str__(self):
        return self.name


class AX12(Dynamixel):
    _registers = Dynamixel._registers.copy()
    _register_maxima = Dynamixel._register_maxima.copy()
    _max_turn_angle = 300

    _registers.update({"down_calibration": 0x14,
                       "up_calibration": 0x16,
                       "cw_compliance_margin": 0x1A,
                       "ccw_compliance_margin": 0x1B,
                       "cw_compliance_slope": 0x1C,
                       "ccw_compliance_slope": 0x1D})

    _register_maxima.update({"cw_compliance_margin": 254,
                             "ccw_compliance_margin": 254,
                             "cw_compliance_slope": 254,
                             "ccw_compliance_slope": 254})
   
    def __init__(self, dx_id, name="AX-12",
                 port="/dev/ttyUSB0", baudrate=1000000, timeout=5):
        super().__init__(dx_id, dx_type="AX-12", name=name,
                         port=port, baudrate=baudrate, timeout=timeout)
        if self.model_number != 12:
            self.close()
            raise DynamixelError("Not an AX-12!")

    @property
    def down_calibration(self):
        return self.read("down_calibration")

    @down_calibration.setter
    def down_calibration(self, value):
        self.write("down_calibration", value)

    @property
    def up_calibration(self):
        return self.read("up_calibration")

    @up_calibration.setter
    def up_calibration(self, value):
        self.write("up_calibration", value)

    @property
    def cw_compliance_margin(self):
        return self.read("cw_compliance_margin")

    @cw_compliance_margin.setter
    def cw_compliance_margin(self, margin):
        self.write("cw_compliance_margin", margin)

    @property
    def ccw_compliance_margin(self):
        return self.read("ccw_compliance_margin")

    @ccw_compliance_margin.setter
    def ccw_compliance_margin(self, margin):
        self.write("ccw_compliance_margin", margin)

    @property
    def compliance_margins(self):
        return self.cw_compliance_margin, self.ccw_compliance_margin

    @compliance_margins.setter
    def compliance_margins(self, margins):
        try:
            cw_margin = margins[0]
            ccw_margin = margins[1]
        except TypeError:
            cw_margin = ccw_margin = margins

        if cw_margin is not None:
            self.cw_compliance_margin = cw_margin
        if ccw_margin is not None:
            self.ccw_compliance_margin = ccw_margin

    @property
    def cw_compliance_slope(self):
        return self.read("cw_compliance_slope")

    @cw_compliance_slope.setter
    def cw_compliance_slope(self, slope):
        self.write("cw_compliance_slope", slope)

    @property
    def ccw_compliance_slope(self):
        return self.read("ccw_compliance_slope")

    @ccw_compliance_slope.setter
    def ccw_compliance_slope(self, slope):
        self.write("ccw_compliance_slope", slope)

    @property
    def compliance_slopes(self):
        return self.cw_compliance_slope, self.ccw_compliance_slope

    @compliance_slopes.setter
    def compliance_slopes(self, slopes):
        try:
            cw_slope = slopes[0]
            ccw_slope = slopes[1]
        except TypeError:
            cw_slope = ccw_slope = slopes

        if cw_slope is not None:
            self.cw_compliance_slope = cw_slope
        if ccw_slope is not None:
            self.ccw_compliance_slope = ccw_slope

    
class MX28(Dynamixel):
    _registers = Dynamixel._registers.copy()
    _register_minima = Dynamixel._register_minima.copy()
    _register_maxima = Dynamixel._register_maxima.copy()
    _two_byte_registers = Dynamixel._two_byte_registers.copy()
    _max_turn_angle = 360

    _registers.update({"multiturn_offset": 0x14,
                       "resolution_divider": 0x16,
                       "p_gain": 0x1A,
                       "i_gain": 0x1B,
                       "d_gain": 0x1C,
                       "present_current": 0x38,
                       "goal_acceleration": 0x49})

    _register_minima.update({"multiturn_offset": -24576,
                             "resolution_divider": 1,
                             "goal_position_multiturn": -28665
                             })

    _register_maxima.update({"multiturn_offset": 24576,
                             "cw_limit": 4095,
                             "ccw_limit": 4095,
                             "resolution_divider": 4,
                             "p_gain": 254,
                             "i_gain": 254,
                             "d_gain": 254,
                             "goal_position": 4095,
                             "goal_position_multiturn": 28665,
                             "goal_acceleration": 254})

    _two_byte_registers.extend(["multiturn_offset", "present_current"])

    def __init__(self, dx_id, name="MX-28",
                 port="/dev/ttyUSB0", baudrate=1000000, timeout=5):
        super().__init__(dx_id, dx_type="MX-28", name=name,
                         port=port, baudrate=baudrate, timeout=timeout)
        if self.model_number != 29:
            self.close()
            raise DynamixelError("Not an MX-28!")

    @property
    def multiturn_offset(self):
        return self.read("multiturn_offset")

    @multiturn_offset.setter
    def multiturn_offset(self, value):
        self.write("multiturn_offset", value)

    @property
    def resolution_divider(self):
        return self.read("resolution_divider")

    @resolution_divider.setter
    def resolution_divider(self, value):
        self.write("resolution_divider", value)

    @property
    def p_gain(self):
        return self.read("p_gain")

    @p_gain.setter
    def p_gain(self, value):
        self.write("p_gain", value)

    @property
    def i_gain(self):
        return self.read("i_gain")

    @i_gain.setter
    def i_gain(self, value):
        self.write("i_gain", value)

    @property
    def d_gain(self):
        return self.read("d_gain")

    @d_gain.setter
    def d_gain(self, value):
        self.write("d_gain", value)

    @property
    def current(self):  # mA
        return self.read("present_current") * 10

    @property
    def goal_acceleration(self):
        return self.read("goal_acceleration")

    @goal_acceleration.setter
    def goal_acceleration(self, value):
        self.write("goal_acceleration", value)
