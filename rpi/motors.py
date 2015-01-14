# (C) 2015  Kyoto University Mechatronics Laboratory
# Released under the GNU General Public License, version 3
from RPi import GPIO as gpio
import logging


class Motor(object):
    """Class for encapsulating motors. Up to 4 motors can be registered.

    Attributes:
        name: The name of the motor.
        motor_id: The motor ID. It is generated automatically.
        pin_fault: GPIO pin for motor Fault line.
        pin_enable: GPIO pin for motor Enable line.
        pin_pwm_pos: GPIO pin for motor PWMP line.
        pin_pwm_neg: GPIO pin for motor PWMN line.
        is_sleeping: A boolean indicating whether the device is sleeping.
        start_input: The input at which the motor starts responding.
        max_speed: The maximum speed to use with the motor.
        motors: A class variable containing all registered motors.
        fault: A class variable indicating whether there was a fault.
    """
    gpio.setmode(gpio.BOARD)
    motors = []
    fault = False

    def __init__(self, name, fault, start_input=0, max_speed=1):
        """Inits and registers the motor.

        Args:
            name: The name of the motor.
            fault: GPIO pin for motor Fault line.
            start_input: (optional) The input at which the motor starts
                responding. Default is 0. Can range between 0 and 1.
            max_speed: (optional) The maximum speed to use with the motor.
                Default is 1. Can range between 0 and 1.

        Raises:
            IndexError: All four motors have been registered.
            ValueError: Bad inputs.
        """
        if Motor.motors[-1].motor_id == 3:
            raise IndexError("4 motors have already been registered.")
        if not 0 <= start_input <= 1:
            raise ValueError("start_input can only range between 0 and 1.")
        if not 0 <= max_speed <= 1:
            raise ValueError("max_speed can only range between 0 and 1.")

        self.logger = logging.getLogger(name)
        self.logger.debug("Initializing motor")
        self.motor_id = len(Motor.motors)
        self.name = name
        self.pin_fault = fault
        self.start_input = start_input
        self.max_speed = max_speed

        self.logger.debug("Setting up fault interrupt")
        gpio.setup(fault, gpio.IN, pull_up_down=gpio.PUD_UP)  # Pull up
        gpio.add_event_detect(fault, gpio.FALLING, callback=self._catch_fault)

        self.logger.debug("Registering motor")
        Motor.motors.append(self)
        self.logger.info("Motor initialized")

    def enable_pwm(self, enable, pwm_pos, pwm_neg, frequency=28000):
        """Allow soft pwm to control the motor.
        
        Args: 
            enable: GPIO pin for the motor driver Enable line.
            pwm_pos: GPIO pin for the motor driver PWMP line.
            pwm_neg: GPIO pin for the motor driver PWMN line.
            frequency: (optional) The frequency of the software pwm.
        """
        self.pin_enable = enable
        self.pin_pwm_pos = pwm_pos
        self.pin_pwm_neg = pwm_neg

        self.logger.debug("Setting up GPIO pins")
        gpio.setup(enable, gpio.OUT)
        gpio.setup(pwm_pos, gpio.OUT)
        gpio.setup(pwm_neg, gpio.OUT)

        self.logger.debug("Starting PWM drivers")
        self.is_sleeping = False
        gpio.output(enable, gpio.HIGH)
        self._fwd = gpio.PWM(pwm_pos, frequency)
        self._rev = gpio.PWM(pwm_neg, frequency)
        self._fwd.start(0)
        self._rev.start(0)

    def enable_serial(self, connection):
        """Allow the use of a USB serial connection.

        Args:
            Connection: A Serial object.
        """
        self.connection = connection

    def _catch_fault(self, channel):
        """Threaded callback for fault detection."""
        self.logger.warning("Fault detected")

    def _scale_speed(self, speed):
        """Get the scaled speed according to input parameters.
            
        Args:
            speed: A value from -1 to 1 indicating the requested speed.
            
        Returns:
            The scaled speed
        """
        # Map (start_input:1) to (0:1)
        if speed > 0:
            speed = (speed * (1 - self.start_input)) + self.start_input
        elif speed < 0:
            speed = (speed * (1 - self.start_input)) - self.start_input

        # Map (0:1) to (0:max_speed)
        speed *= self.max_speed
        speed = round(speed, 4)
        return speed

    def drive(self, speed):
        """Set the motor to a given speed.

        Args:
            speed: A value from -1 to 1 indicating the requested speed of the
                motor. The speed is changed by changing the PWM duty cycle.
        """
        speed = self._scale_speed(speed)

        if self.is_sleeping:
            self.logger.info("Waking up")
            gpio.output(self.pin_enable, gpio.HIGH)
        try:
            if speed < 0:
                self._fwd.ChangeDutyCycle(0)
                self._rev.ChangeDutyCycle(-speed * 100)
            else:
                self._fwd.ChangeDutyCycle(speed * 100)
                self._rev.ChangeDutyCycle(0)
        except AttributeError:
            self.logger.error("Cannot drive! Direct control not enabled.")

    def transmit(self, speed):
        """Send a byte through a serial connection.
            
            Args:
                speed: A value from -1 to 1 indicating the requested speed.
        """
        speed = self._scale_speed(speed)
        top = self.motor_id << 6
        mid = 1 << 5 if speed < 0 else 0
        lower = int(abs(speed) * 31)
        byte = bytes([top + mid + lower])
        try:
            self.connection.write(byte)
        except AttributeError:
            self.logger.error("Cannot transmit! Serial comms not enabled.")

    def sleep(self):
        """Put the motor driver to sleep to save power."""
        self.logger.info("Going to sleep")
        try:
            gpio.output(self.pin_enable, gpio.LOW)
            self.is_sleeping = True
        except AttributeError:
            self.logger.error("Cannot sleep! Direct control not enabled.")

    def shut_down(self):
        """Shut down and deregister the motor."""
        self.logger.debug("Shutting down motor")
        self.logger.debug("Stopping motor")
        self._fwd.stop()
        self._rev.stop()

        self.logger.debug("Deregistering motor")
        Motor.motors.remove(self)
        self.logger.info("Motor shut down")

    @classmethod
    def shut_down_all(self):
        """A class method to shut down and deregister all motors."""
        logging.info("Shutting down all motors.")
        for motor in Motor.motors:
            motor.shut_down()
        gpio.cleanup()
        logging.info("All motors shut down")

    def __repr__(self):
        return "{} (ID# {})".format(self.name, self.motor_id)

    def __str__(self):
        return self.name
