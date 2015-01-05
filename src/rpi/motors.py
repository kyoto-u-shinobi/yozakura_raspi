# (C) 2015  Kyoto University Mechatronics Laboratory
# Released under the GNU General Public License, version 3
from RPi import GPIO as gpio
import wiringpi2 as wiringpi
import logging

class Motor(object):
    motors = {}
    gpio.setmode(gpio.BOARD)
    wiringpi.wiringPiSetupPhys()

    def __init__(self, enable, pwm_pos, pwm_neg, fault, name, frequency=28000, hard=False):
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

        # Setup all pins
        gpio.setup(enable, gpio.OUT)
        gpio.setup(fault, gpio.IN)
        gpio.setup(pwm_pos, gpio.OUT)
        gpio.setup(pwm_neg, gpio.OUT)

        # Start PWM drivers
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

        Motor.motors[self] = name
        self.logger.info("Motor initialized")

    def drive(self, speed):
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
        self.logger.info("Going to sleep")
        gpio.output(self.pin_enable, gpio.LOW)
        self.is_sleeping = True

    def shut_down(self):
        self.logger.debug("Shutting down motor")
        gpio.output(self.pin_enable, gpio.LOW)
        if self.hard:
            wiringpi.pwmWrite(self.pin_pwm_pos, 0)
            wiringpi.pwmWrite(self.pin_pwm_neg, 0)
        else:
            self._fwd.stop()
            self._rev.stop()
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
