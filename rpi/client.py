# (C) 2015  Kyoto University Mechatronics Laboratory
# Released under the GNU General Public License, version 3
import pickle
import socket
import time

from ..common.networking import ClientBase


class Client(ClientBase):
    """A client to communicate with the server and control the robot.

    Attributes:
        request: A socket object handling communication with the server.
        motors: A dictionary containing all registered motors.
        wheels_single_stick: A boolean indicating whether the wheels are
            controlled by only one stick (i.e., the left analog stick).
    """
    def __init__(self, server_address):
        """Inits the client.

        Args:
            server_address: The address on which the server is listening. This
                is a tuple containing a string giving the address, and an
                integer port number.
        """
        super().__init__(server_address)
        self.request.settimeout(0.5)
        self.motors = {}

    def run(self):
        """Send and handle requests until a KeyboardInterrupt is received."""
        if not self.motors:
            self.logger.critical("No motors registered!")
            return

        self.logger.info("Client started")
        self._timestamp = time.time()
        self.wheels_single_stick = False
        timed_out = False

        while True:
            try:
                try:
                    self.send("wheels")
                    result = self.receive()
                except socket.timeout:
                    if not timed_out:
                        self.logger.warning("Lost connection with base station")
                        self.logger.info("Turning off motors")
                        for motor in self.motors.values():
                            motor.drive(0)
                        timed_out = True
                    continue

                if timed_out:
                    timed_out = False

                state = pickle.loads(result)
                self._handle_input(state)

            except (KeyboardInterrupt, RuntimeError):
                break

    def _handle_input(self, state):
        """Handle input from the joystick.

        Inputs handled:
            select: Toggle the control mode between single and dual analog
                sticks.
            lstick: x- and y- axes control wheels in single-stick mode; y-axis
                controls left-side wheels in dual-stick mode.
            rstick: y-axis controls right-side wheels in dual-stick mode.

        Args:
            state: A state object representing the controller state.
        """
        dpad, lstick, rstick, buttons = state.data

        if buttons.buttons[8]:  # The select button was pressed
            self._switch_control_mode()

        if self.wheels_single_stick:
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

    def _switch_control_mode(self):
        """Toggle the control mode between single and dual analog sticks.

        Ignores the toggle directive if the mode has been switched within the
        last second.
        """
        current_time = time.time()

        if current_time - self._timestamp >= 1:
            if self.wheels_single_stick:
                self.wheels_single_stick = False
                self.logger.info("Control mode switched: Use " +\
                                 "lstick and rstick to control robot")
            else:
                self.wheels_single_stick = True
                self.logger.info("Control mode switched: Use " +\
                                 "lstick to control robot")
            self._timestamp = current_time

    def add_motor(self, motor, ser=None, pwm_pins=None):
        """Set up and register a motor.

        Args:
            motor: The motor to be registered.
            ser: (optional) The serial connection to communicate with the
                microcontroller to which the motor drivers are connected. This
                is necessary in order to use hardware PWM. Default is None.
            pwm_pins: (optional)
        """
        self.logger.debug("Adding motor {}".format(motor))
        if pwm_pins is not None:
            motor.enable_pwm(*pwm_pins)
        if ser is not None:
            motor.enable_serial(ser)

        self.motors[motor.name] = motor

    def remove_motor(self, motor):
        """Deregister a motor.

        Args:
            motor: The motor to be deregistered.
        """
        self.logger.debug("Removing motor {}".format(motor))
        del self.motors[motor.name]
