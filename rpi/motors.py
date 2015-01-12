# (C) 2015  Kyoto University Mechatronics Laboratory
# Released under the GNU General Public License, version 3
from RPi import GPIO as gpio
import wiringpi2 as wiringpi
import logging


class Motor(object):
    """Class for encapsulating motors.

    Attributes:
        pin_enable: GPIO pin for motor Enable line.
        pin_pwm_pos: GPIO pin for motor PWMP line.
        pin_pwm_neg: GPIO pin for motor PWMN line.
        pin_fault: GPIO pin for motor Fault line.
        name: The name of the motor.
        is_sleeping: A boolean indicating whether the device is sleeping.
        hard: Whether to use hardware pwm. Default is False.
        start_input: The input at which the motor starts
        max_speed: The maximum speed to use with the motor.
        motor_id: The motor ID.
        motors: A class variable containing all registered motors.
        fault: A class variable indicating whether there was a fault.
    """
    motors = {}
    fault = False
    gpio.setmode(gpio.BOARD)
    wiringpi.wiringPiSetupPhys()

    def __init__(self, enable, pwm_pos, pwm_neg, fault, name, motor_id,
            frequency=28000, hard=False, start_input=0, max_speed=1):
        """Inits and registers the motor.

        Args:
            enable: GPIO pin for motor Enable line.
            pwm_pos: GPIO pin for motor PWMP line.
            pwm_neg: GPIO pin for motor PWMN line.
            fault: GPIO pin for motor Fault line.
            name: The name of the motor.
            motor_id: The motor ID. An integer be between 0 and 3.
            frequency: (optional) The frequency of the software pwm.
            hard: (optional) Whether to use hardware pwm. Default is False.
            start_input: (optional) The input at which the motor starts
                responding. Default is 0. Can range between 0 and 1.
            max_speed: (optional) The maximum speed to use with the motor.
                Default is 1. Can range between 0 and 1.

        Raises:
            KeyError: Another motor has been registered with the same name.
        """
        if motor_id in Motor.motors.values():
            raise KeyError("This ID is already in use.")
        if not 0 <= start_input <= 1:
            raise ValueError("start_input can only range between 0 and 1.")
        if not 0 <= max_speed <= 1:
            raise ValueError("max_speed can only range between 0 and 1.")
        if not 0 <= motor_id <= 3:
            raise ValueError("The motor ID can only range between 0 and 3.")
        self.logger = logging.getLogger(name)
        self.logger.debug("Initializing motor")
        self.pin_enable = enable
        self.pin_pwm_pos = pwm_pos
        self.pin_pwm_neg = pwm_neg
        self.pin_fault = fault
        self.name = name
        self.motor_id = motor_id
        self.hard = hard
        self.start_input = start_input
        self.max_speed = max_speed

        self.logger.debug("Setting up GPIO pins")
        gpio.setup(enable, gpio.OUT)
        gpio.setup(pwm_pos, gpio.OUT)
        gpio.setup(pwm_neg, gpio.OUT)

        self.logger.debug("Setting up interrupt")
        gpio.setup(fault, gpio.IN, pull_up_down=gpio.PUD_UP)  # Pull up
        gpio.add_event_detect(fault, gpio.FALLING, callback=self._catch_fault)

        self.logger.debug("Starting PWM drivers")
        self.is_sleeping = False
        if not hard:
            gpio.output(enable, gpio.HIGH)
            self._fwd = gpio.PWM(pwm_pos, frequency)
            self._rev = gpio.PWM(pwm_neg, frequency)
            self._fwd.start(0)
            self._rev.start(0)
        else:
            gpio.output(pwm_pos, gpio.LOW)
            gpio.output(pwm_neg, gpio.LOW)
            wiringpi.pinMode(enable, 2)
            wiringpi.pwmWrite(enable, 0)

        self.logger.debug("Registering motor")
        Motor.motors[self] = motor_id
        self.logger.info("Motor initialized")

    def _catch_fault(self, channel):
        """Threaded callback for fault detection."""
        self.logger.warning("Fault detected")
        #Motor.fault = True
        #Motor.shut_down_all()

    def _scale_speed(self, speed):
        """Get the scaled speed according to input parameters.
            
        Args:
            speed: A value from -1 to 1 indicating the requested speed.
            
        Returns:
            The scaled speed
        """
        # Map (start_input) to (0:1)
        if speed > 0:
            speed = (speed * (1 - self.start_input)) + self.start_input
        elif speed < 0:
            speed = (speed * (1 - self.start_input)) - self.start_input
        speed *= self.max_speed  # Map (0:1) to (0:max_speed)
        speed = round(speed, 4)
        return speed

    def drive(self, speed):
        """Set the motor to a given speed.

        Args:
            speed: A value from -1 to 1 indicating the requested speed of the
                motor. The speed is changed by changing the PWM duty cycle.
        """
        speed = self._scale_speed(speed)

        if self.is_sleeping and not self.hard:
            self.logger.info("Waking up")
            gpio.output(self.pin_enable, gpio.HIGH)
        if speed < 0:
            if self.hard:
                gpio.output(self.pin_pwm_pos, gpio.LOW)
                gpio.output(self.pin_pwm_neg, gpio.HIGH)
                wiringpi.pwmWrite(self.pin_enable, int(-speed * 1024))
            else:
                self._fwd.ChangeDutyCycle(0)
                self._rev.ChangeDutyCycle(-speed * 100)
        else:
            if self.hard:
                gpio.output(self.pin_pwm_pos, gpio.HIGH)
                gpio.output(self.pin_pwm_neg, gpio.LOW)
                wiringpi.pwmWrite(self.pin_enable, int(speed * 1024))
            else:
                self._fwd.ChangeDutyCycle(speed * 100)
                self._rev.ChangeDutyCycle(0)

    def _encode_byte(self, speed):
        """Create a byte containing the motor ID and speed information.
            
            Args:
                speed: A value from -1 to 1 indicating the requested speed.
            
            Returns:
                The encoded byte.
        """
        speed = self._scale_speed(speed)
        top = self.motor_id << 6
        mid = 1 << 5 if speed < 0 else 0
        lower = int(abs(speed) * 31)
        return bytes([top + mid + lower])

    def send_byte(self, speed, ser):
        """Send a byte through a serial connection.
            
            Args:
                speed: A value from -1 to 1 indicating the requested speed.
                ser: A Serial object.
        """
        byte = self._encode_byte(speed)
        ser.write(byte)

    def sleep(self):
        """Put the motor driver to sleep to save power."""
        self.logger.info("Going to sleep")
        if not self.hard:
            gpio.output(self.pin_enable, gpio.LOW)
            self.is_sleeping = True

    def shut_down(self):
        """Shut down and deregister the motor."""
        self.logger.debug("Shutting down motor")
        self.logger.debug("Stopping motor")
        if self.hard:
            wiringpi.pwmWrite(self.pin_enable, 0)
        else:
            self._fwd.stop()
            self._rev.stop()
        self.logger.debug("Cleaning up pins.")

        self.logger.debug("Deregistering motor")
        del Motor.motors[self]
        self.logger.info("Motor shut down")

    @classmethod
    def shut_down_all(self):
        """A class method to shut down and deregister all motors."""
        logging.info("Shutting down all motors.")
        for motor in list(Motor.motors.keys()):
            motor.shut_down()
        gpio.cleanup()
        logging.info("All motors shut down")

    def __repr__(self):
        return self.name

    def __str__(self):
        return self.name
