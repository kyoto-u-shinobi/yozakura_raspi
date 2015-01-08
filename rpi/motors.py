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
        motors: A class variable containing all registered motors.
        hard: (optional) Whether to use hardware pwm. Default is False.

    """
    motors = {}
    gpio.setmode(gpio.BOARD)
    wiringpi.wiringPiSetupPhys()

    def __init__(self, enable, pwm_pos, pwm_neg, fault, name, frequency=28000,
                 hard=False):
        """Inits and registers the motor.

        Args:
            enable: GPIO pin for motor Enable line.
            pwm_pos: GPIO pin for motor PWMP line.
            pwm_neg: GPIO pin for motor PWMN line.
            fault: GPIO pin for motor Fault line.
            name: The name of the motor.
            frequency: (optional) The frequency of the software pwm.
            hard: (optional) Whether to use hardware pwm. Default is False.

        Raises:
            KeyError: Another motor has been registered with the same name.
        """
        if name in Motor.motors.values():
            raise KeyError("This name is already in use.")
            return
        self.logger = logging.getLogger(name)
        self.logger.debug("Initializing motor")
        self.pin_enable = enable
        self.pin_pwm_pos = pwm_pos
        self.pin_pwm_neg = pwm_neg
        self.pin_fault = fault
        self.name = name
        self.hard = hard

        self.logger.debug("Setting up GPIO pins")
        gpio.setup(enable, gpio.OUT)
        gpio.setup(pwm_pos, gpio.OUT)
        gpio.setup(pwm_neg, gpio.OUT)
        gpio.setup(fault, gpio.IN)

        self.logger.debug("Starting PWM drivers")
        gpio.output(enable, gpio.HIGH)
        self.is_sleeping = False
        if not hard:
            self._fwd = gpio.PWM(pwm_pos, frequency)
            self._rev = gpio.PWM(pwm_neg, frequency)
            self._fwd.start(0)
            self._rev.start(0)
        else:
            wiringpi.pinMode(pwm_pos, 2)
            wiringpi.pinMode(pwm_neg, 1)
            wiringpi.pwmWrite(pwm_pos, 0)
            wiringpi.digitalWrite(pwm_neg, 0)

        self.logger.debug("Registering motor")
        Motor.motors[self] = name
        self.logger.info("Motor initialized")

    def drive(self, speed):
        """Set the motor to a given speed.

        Args:
            speed: A value from -1 to 1 indicating the requested speed of the
                motor. The speed is changed by changing the PWM duty cycle.
        """
        if self.hard:
            speed = (speed * 0.3) + (0.7 if speed > 0 else -0.7)
        speed = round(speed, 4)
        if self.is_sleeping:
            self.logger.info("Waking up")
            gpio.output(self.pin_enable, gpio.HIGH)
        if speed < 0:
            if self.hard:
                wiringpi.digitalWrite(self.pin_pwm_pos, 0)
                wiringpi.pwmWrite(self.pin_pwm_neg, int(-speed * 1024))
            else:
                self._fwd.ChangeDutyCycle(0)
                self._rev.ChangeDutyCycle(-speed * 100)
        else:
            if self.hard:
                wiringpi.pwmWrite(self.pin_pwm_pos, int(speed * 1024))
                wiringpi.digitalWrite(self.pin_pwm_neg, 0)
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
        if self.hard:
            wiringpi.pwmWrite(self.pin_pwm_pos, 0)
            wiringpi.pwmWrite(self.pin_pwm_neg, 0)
        else:
            self._fwd.stop()
            self._rev.stop()
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
