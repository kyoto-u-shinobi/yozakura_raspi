# (C) 2015  Kyoto University Mechatronics Laboratory
# Released under the GNU General Public License, version 3
from RPi import GPIO as gpio
import logging


class Motor(object):
    motors = {}
    gpio.setmode(gpio.BOARD)

    def __init__(self, enable, pwm_pos, pwm_neg, fault, name):
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

            # Setup all pins
            gpio.setup(enable, gpio.OUT)
            gpio.setup(pwm_pos, gpio.OUT)
            gpio.setup(pwm_neg, gpio.OUT)
            gpio.setup(fault, gpio.IN)

            # Start PWM drivers
            gpio.output(enable, gpio.HIGH)
            self.is_sleeping = False
            self._fwd = gpio.PWM(pwm_pos, 50)  # 50 Hz
            self._rev = gpio.PWM(pwm_neg, 50)  # 50 Hz
            self._fwd.start(0)
            self._rev.start(0)

            Motor.motors[self] = name
            self.logger.info("Motor initialized")

    def drive(speed):
        if is_sleeping:
            self.logger.info("Waking up")
            gpio.output(self.pin_enable, gpio.HIGH)
        if speed < 0:
            self._fwd.ChangeDutyCycle(0)
            self._rev.ChangeDutyCycle(-speed * 100)
        else:
            self._fwd.ChangeDutyCycle(speed * 100)
            self._rev.ChangeDutyCycle(0)

    def sleep(self):
        self.logger.info("Going to sleep")
        gpio.output(self.pin_enable, gpio.LOW)
        self.is_sleeping = True

    def shut_down(self):
        self.logger.debug("Shutting down motor")
        self._fwd.stop()
        self._rev.stop()
        gpio.output(self.pin_enable, gpio.LOW)
        gpio.output(self.pin_pwm_pos, gpio.LOW)
        gpio.output(self.pin_pwm_neg, gpio.LOW)
        gpio.cleanup()
        del Motor.motors[self]
        self.logger.info("Motor shut down")

    @classmethod
    def shut_down_all(self):
        logging.info("Shutting down all motors.")
        for motor in list(Motor.motors.keys()):
            motor.shut_down()

    def __repr__(self):
        return self.name

    def __str__(self):
        return self.name
