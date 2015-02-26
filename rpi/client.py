# (C) 2015  Kyoto University Mechatronics Laboratory
# Released under the GNU General Public License, version 3
import pickle
import socket

from ..common.networking import TCPClientBase


class Client(TCPClientBase):
    """A client to communicate with the server and control the robot.

    Attributes:
        request: A socket object handling communication with the server.
        motors: A dictionary containing all registered motors.
        serials: A dictionary containing all the registered serial conns.
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
        self.serials = {}

    def run(self):
        """Send and handle requests until a KeyboardInterrupt is received."""
        if not self.motors:
            self.logger.critical("No motors registered!")
            return

        self.logger.info("Client started")
        timed_out = False

        while True:
            try:
                try:
                    self.send("speeds")
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

                # Get flipper positions
                positions = self.serials["mbed_flipper"].readline()
                lpos, rpos = [int(i, 0) / 0xFFFF for i in positions.split()]

                lmotor, rmotor, lflipper, rflipper = pickle.loads(result)
                self.motors["left_motor"].drive(lmotor)
                self.motors["right_motor"].drive(rmotor)

                # TODO(masasin): Hold position if input is 0.
                self.motors["left_flipper"].drive(lflipper)
                self.motors["right_flipper"].drive(rflipper)

            except (KeyboardInterrupt, RuntimeError):
                break

    def add_serial_device(self, name, device):
        """Register a serial device for ADC communication.

        Args:
            name: The name of the device.
            device: The serial connection to the microcontroller.
        """
        self.logger.debug("Registering {}".format(name))
        self.serials[name] = device

    def add_motor(self, motor, ser=None, pwm_pins=None):
        """Set up and register a motor.

        Args:
            motor: The motor to be registered.
            ser: (optional) The serial connection to communicate with the
                microcontroller to which the motor drivers are connected. This
                is necessary in order to use hardware PWM. Default is None.
            pwm_pins: (optional) The pins used for soft PWM. Default is None.
        """
        self.logger.debug("Adding motor {}".format(motor))
        if pwm_pins is not None:
            motor.enable_pwm(*pwm_pins)
        if ser is not None:
            motor.enable_serial(ser)

        self.motors[motor.name] = motor

    def remove_serial_device(self, name):
        """Deregister a serial device.

        Args:
            name: The name of the device to be deregistered.
        """
        self.logger.debug("Removing {}".format(name))
        del self.serials[name]

    def remove_motor(self, motor):
        """Deregister a motor.

        Args:
            motor: The motor to be deregistered.
        """
        self.logger.debug("Removing motor {}".format(motor))
        del self.motors[motor.name]
