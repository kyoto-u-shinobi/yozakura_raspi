# (C) 2015  Kyoto University Mechatronics Laboratory
# Released under the GNU General Public License, version 3
from RPi import GPIO as gpio
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
        motors: A class variable containing all registered motors.
    """
    motors = {}
    gpio.setmode(gpio.BOARD)

    def __init__(self, enable, pwm_pos, pwm_neg, fault, name):
        """Inits and registers the motor.

        Args:
            enable: GPIO pin for motor Enable line.
            pwm_pos: GPIO pin for motor PWMP line.
            pwm_neg: GPIO pin for motor PWMN line.
            fault: GPIO pin for motor Fault line.
            name: The name of the motor.

        Raises:
            KeyError: Another motor has been registered with the same name.
        """
        if name in Motor.motors.values():
            raise KeyError("This name is already in use.")
        else:
            self.logger = logging.getLogger("{}".format(name))
            self.logger.debug("Initializing motor".format(name))
            self.pin_enable = enable
            self.pin_pwm_pos = pwm_pos
            self.pin_pwm_neg = pwm_neg
            self.pin_fault = fault
            self.name = name

            self.logger.debug("Setting up GPIO pins")
            gpio.setup(enable, gpio.OUT)
            gpio.setup(pwm_pos, gpio.OUT)
            gpio.setup(pwm_neg, gpio.OUT)
            gpio.setup(fault, gpio.IN)

            self.logger.debug("Starting PWM drivers")
            gpio.output(enable, gpio.HIGH)
            self.is_sleeping = False
            self._fwd = gpio.PWM(pwm_pos, 50)  # 50 Hz
            self._rev = gpio.PWM(pwm_neg, 50)  # 50 Hz
            self._fwd.start(0)
            self._rev.start(0)

            self.logger.debug("Registering motor")
            Motor.motors[self] = name
            self.logger.info("Motor initialized")

    def drive(self, speed):
        """Set the motor to a given speed.

        Args:
            speed: A value from -1 to 1 indicating the requested speed of the
                motor. The speed is changed by changing the PWM duty cycle.
        """
        if self.is_sleeping:
            self.logger.info("Waking up")
            gpio.output(self.pin_enable, gpio.HIGH)
        if speed < 0:
            self._fwd.ChangeDutyCycle(0)
            self._rev.ChangeDutyCycle(-speed * 100)
        else:
            self._fwd.ChangeDutyCycle(speed * 100)
            self._rev.ChangeDutyCycle(0)

    def sleep(self):
        """Put the motor driver to sleep to save power."""
        self.logger.info("Going to sleep")
        gpio.output(self.pin_enable, gpio.LOW)
        self.is_sleeping = True

    def shut_down(self):
        """Shut down and deregister the motor."""
        self.logger.debug("Shutting down motor")
        self.logger.debug("Stopping motor")
        self._fwd.stop()
        self._rev.stop()

        self.logger.debug("Cleaning up pins.")
        gpio.output(self.pin_enable, gpio.LOW)
        gpio.output(self.pin_pwm_pos, gpio.LOW)
        gpio.output(self.pin_pwm_neg, gpio.LOW)
        gpio.cleanup()

        self.logger.debug("Deregistering motor")
        del Motor.motors[self]
        self.logger.info("Motor shut down")

    @classmethod
    def shut_down_all(self):
        """A class method to shut down and deregister all motors."""
        logging.info("Shutting down all motors.")
        for motor in list(Motor.motors.keys()):
            motor.shut_down()

    def __repr__(self):
        return self.name

    def __str__(self):
        return self.name
