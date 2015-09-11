from nose.tools import assert_equal, assert_true, assert_false, raises
from unittest.mock import patch, MagicMock

MockRPi = MagicMock()
modules = {
    "RPi": MockRPi,
    "RPi.GPIO": MockRPi.GPIO
}
patcher = patch.dict("sys.modules", modules)
patcher.start()


def teardown_module():
    patcher.stop()

import time

from common.exceptions import BadArgError, MotorCountError, NoDriversError

from rpi.motor import gpio, Motor


class TestMotor(object):
    def teardown(self):
        Motor.shutdown_all()


class TestAddMotor(TestMotor):
    def test_motor_default_attributes(self):
        motor0 = Motor("motor0", 8, 10, 7)
        assert_equal(motor0.start_input, 0)
        assert_equal(motor0.max_speed, 1)
        assert_false(motor0.has_serial)
        assert_false(motor0.has_pwm)

    def test_motor_wiring(self):
        Motor("motor0", 8, 10, 7)
        gpio.setmode.assert_called_once_with(gpio.BOARD)
        gpio.setwarnings.assert_called_once_with(False)

    def test_can_add_four_motors(self):
        assert_equal(Motor.motors, [])
        motor0 = Motor("motor0", 8, 10, 7)
        motor1 = Motor("motor1", 8, 10, 7, start_input=0.5)
        motor2 = Motor("motor2", 8, 10, 7, max_speed=0.5)
        motor3 = Motor("motor3", 8, 10, 7, start_input=0.5, max_speed=0.5)
        assert_equal(Motor.motors, [motor0, motor1, motor2, motor3])

    @raises(MotorCountError)
    def test_cannot_add_more_than_four_motors(self):
        Motor("motor0", 8, 10, 7)
        Motor("motor1", 8, 10, 7)
        Motor("motor2", 8, 10, 7)
        Motor("motor3", 8, 10, 7)
        Motor("motor4", 8, 10, 7)

    @raises(BadArgError)
    def test_start_input_cannot_be_negative(self):
        Motor("motor0", 8, 10, 7, start_input=-0.5)

    @raises(BadArgError)
    def test_start_input_cannot_be_more_than_one(self):
        Motor("motor0", 8, 10, 7, start_input=1.5)

    @raises(BadArgError)
    def test_max_speed_cannot_be_negative(self):
        Motor("motor0", 8, 10, 7, max_speed=-0.5)

    @raises(BadArgError)
    def test_max_speed_cannot_be_more_than_one(self):
        Motor("motor0", 8, 10, 7, max_speed=1.5)


class TestEnableMotorDrive(TestMotor):
    def setup(self):
        self.motor0 = Motor("motor0", 8, 10, 7)

    def test_enable_serial(self):
        MockSerial = MagicMock()
        ser = MockSerial("/dev/ttyACM0", baudrate=38400)
        self.motor0.enable_serial(ser)
        assert_true(self.motor0.has_serial)
        assert_equal(self.motor0.ser, ser)

    def test_enable_soft_pwm(self):
        self.motor0.enable_soft_pwm(12, 17, 2800)
        assert_equal(self.motor0.pin_pwm, 12)
        assert_equal(self.motor0.pin_dir, 17)
        assert_true(self.motor0.has_pwm)
        gpio.setup.assert_any_call(self.motor0.pin_pwm, gpio.OUT)
        gpio.setup.assert_any_call(self.motor0.pin_dir, gpio.OUT)
        gpio.PWM.assert_called_with(12, 2800)


class TestMotorUtilities(TestMotor):
    def test_reset_driver(self):
        motor0 = Motor("motor0", 8, 10, 7)
        time_start = time.time()
        motor0.reset_driver()
        time_end = time.time()
        gpio.output.assert_any_call(motor0.pin_reset, gpio.LOW)
        gpio.output.assert_any_call(motor0.pin_reset, gpio.HIGH)
        assert_true(time_end >= time_start + 0.05)

    def test_shutdown_all(self):
        Motor("motor0", 8, 10, 7)
        Motor("motor1", 8, 10, 7)
        Motor("motor2", 8, 10, 7)
        Motor("motor3", 8, 10, 7)
        Motor.shutdown_all()
        gpio.cleanup.assert_called_once()
        assert_equal(Motor.motors, [])


class TestMotorDrive(TestMotor):
    def setup(self):
        self.motor0 = Motor("motor0", 8, 10, 7)
        MockSerial = MagicMock()
        ser = MockSerial("/dev/ttyACM0", baudrate=38400)
        self.ser = ser

    @raises(NoDriversError)
    def test_drive_without_drivers_raises_error(self):
        self.motor0.drive(0.5)

    @raises(BadArgError)
    def test_drive_speed_more_than_one(self):
        self.motor0.drive(1.5)

    @raises(BadArgError)
    def test_drive_speed_less_than_minus_one(self):
        self.motor0.drive(-1.5)

    @patch.object(Motor, "_scale_speed", autospec=True)
    def test_drive_automatically_scales_speed(self, mock_scale_speed):
        mock_scale_speed.return_value = 0.3
        try:
            self.motor0.drive(0.5)
        except NoDriversError:
            pass
        mock_scale_speed.assert_called_once_with(self.motor0, 0.5)

    @patch.object(Motor, "_scale_speed", autospec=True)
    def test_drive_with_soft_pwm_and_serial(self, mock_scale_speed):
        mock_scale_speed.return_value = 0.3
        self.motor0.enable_serial(self.ser)
        self.motor0.enable_soft_pwm(12, 17, 2800)
        self.motor0.drive(0.5)
        self.motor0.ser.write.assert_called_with(bytes([0b01001000]))  # 0.3

    @patch.object(Motor, "_scale_speed", autospec=True)
    def test_drive_calls_soft_pwm(self, mock_scale_speed):
        mock_scale_speed.return_value = 0.3
        self.motor0.enable_soft_pwm(12, 17, 2800)
        self.motor0.drive(0.5)
        gpio.output.assert_called_with(self.motor0.pin_dir, gpio.HIGH)
        self.motor0._pwm.ChangeDutyCycle.assert_called_with(30)

    @patch.object(Motor, "_scale_speed", autospec=True)
    def test_drive_calls_serial(self, mock_scale_speed):
        mock_scale_speed.return_value = 0.3
        self.motor0.enable_serial(self.ser)
        self.motor0.drive(0.5)
        self.motor0.ser.write.assert_called_with(bytes([0b01001000]))  # 0.3

    def test_drive_with_soft_pwm_fwd(self):
        self.motor0.enable_soft_pwm(12, 17, 2800)
        self.motor0.drive(0.3)
        gpio.output.assert_called_with(self.motor0.pin_dir, gpio.HIGH)
        self.motor0._pwm.ChangeDutyCycle.assert_called_with(30)

    def test_drive_with_soft_pwm_back(self):
        self.motor0.enable_soft_pwm(12, 17, 2800)
        self.motor0.drive(-0.3)
        gpio.output.assert_called_with(self.motor0.pin_dir, gpio.LOW)
        self.motor0._pwm.ChangeDutyCycle.assert_called_with(30)

    def test_drive_with_soft_pwm_zero(self):
        self.motor0.enable_soft_pwm(12, 17, 2800)
        self.motor0.drive(0)
        gpio.output.assert_called_with(self.motor0.pin_dir, gpio.LOW)
        self.motor0._pwm.ChangeDutyCycle.assert_called_with(0)

    def test_drive_with_serial_fwd(self):
        self.motor0.enable_serial(self.ser)
        self.motor0.drive(0.3)
        self.motor0.ser.write.assert_called_with(bytes([0b01001000]))  # 0.3

    def test_drive_with_serial_back(self):
        self.motor0.enable_serial(self.ser)
        self.motor0.drive(-0.3)
        self.motor0.ser.write.assert_called_with(bytes([0b01001100]))  # -0.3

    def test_drive_with_serial_zero(self):
        self.motor0.enable_serial(self.ser)
        self.motor0.drive(0)
        self.motor0.ser.write.assert_called_with(bytes([0b00000000]))  # 0

    def test_drive_with_serial_uses_motor_id(self):
        motor1 = Motor("motor1", 8, 10, 7)
        motor1.enable_serial(self.ser)
        motor1.drive(0.5)
        motor1.ser.write.assert_called_with(bytes([0b01111001]))  # 0.5, motor 1

    def test_scale_speed(self):
        start_input_list = [0, 0.2, 0, 0.2]
        max_speed_list = [1, 1, 0.8, 0.8]
        input_speeds = [-1, -0.5, -0.1, 0, 0.1, 0.5, 1]
        expected_speeds = {
            -1: [-1, -1, -0.8, -0.8],
            -0.5: [-0.5, -0.6, -0.4, -0.48],
            -0.1: [-0.1, -0.28, -0.08, -0.224],
            0: [0, 0, 0, 0],
            0.1: [0.1, 0.28, 0.08, 0.224],
            0.5: [0.5, 0.6, 0.4, 0.48],
            1: [1, 1, 0.8, 0.8]
        }

        for speed in input_speeds:
            scaled_speeds = []
            for start_input, max_speed in zip(start_input_list, max_speed_list):
                self.motor0.start_input = start_input
                self.motor0.max_speed = max_speed
                scaled_speeds.append(self.motor0._scale_speed(speed))
            assert_equal(scaled_speeds, expected_speeds[speed])
