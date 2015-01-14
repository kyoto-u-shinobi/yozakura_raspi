# (C) 2015  Kyoto University Mechatronics Laboratory
# Released under the GNU General Public License, version 3
from common.networking import ClientBase
import pickle
import socket
import time


class Client(ClientBase):
    def __init__(self, server_address):
        super().__init__(server_address)
        self.request.settimeout(0.5)
        self.motors = {}

    def run(self):
        if not self.motors:
            self.logger.critical("No motors registered!")
            return

        self.timestamp = time.time()
        self.body_single_stick = False
        timeout_mode = False

        while True:
            try:
                try:
                    self.send("body")
                    result = self.receive()
                except socket.timeout:
                    if not timeout_mode:
                        timeout_mode = True
                        self.logger.warning("Lost connection with base station")
                        self.logger.info("Turning off motors")
                        self.turn_off_motors()
                    continue

                if timeout_mode:
                    timeout_mode = False

                dpad, lstick, rstick, buttons = pickle.loads(result).data
                if buttons.buttons[8]:  # The select button was pressed
                    self.switch_control_mode()

                if self.body_single_stick:
                    self.logger.debug("lx: {:9.7}  ly: {:9.7}".format(lstick.x,
                                                                      lstick.y))
                    if abs(lstick.y) < 0.1:  # Rotate in place
                        self.motors["left_motor"].drive(lstick.x)
                        self.motors["right_motor"].drive(-lstick.x)
                    else:
                        l_mult = (1 + lstick.x) / (1 + abs(lstick.x))
                        r_mult = (1 - lstick.x) / (1 + abs(lstick.x))
                        self.motors["left_motor"].drive(-lstick.y * l_mult)
                        self.motors["right_motor"].drive(-lstick.y * r_mult)
                else:
                    self.logger.debug("ly: {:9.7}  ry: {:9.7}".format(lstick.y,
                                                                      rstick.y))
                    self.motors["left_motor"].drive(-lstick.y)
                    self.motors["right_motor"].drive(-rstick.y)

            except (KeyboardInterrupt, RuntimeError):
                break

    def add_motor(self, motor, pwm_pins=None, ser=None):
        if pwm_pins is not None:
            motor.enable_pwm(*pwm_pins)
        if ser is not None:
            motor.enable_serial(ser)

        self.motors[motor.name] = motor

    def remove_motor(self, motor):
        del self.motors[motor.name]

    def turn_off_motors(self):
        for motor in self.motors.values():
            if self.has_serial:
                motor.send_byte(0)
            if self.has_pwm:
                motor.drive(0)

    def switch_control_mode(self):
        current_time = time.time()
        if current_time - self.timestamp >= 1:  # Debounce for 1 second.
            if self.body_single_stick:
                self.body_single_stick = False
                self.logger.info("Control mode switched: Use " +\
                                 "lstick and rstick to control robot")
            else:
                self.body_single_stick = True
                self.logger.info("Control mode switched: Use " +\
                                 "lstick to control robot")
            self.timestamp = current_time
