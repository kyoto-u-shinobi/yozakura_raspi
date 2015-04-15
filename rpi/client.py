# (C) 2015  Kyoto University Mechatronics Laboratory
# Released under the GNU General Public License, version 3
"""
Manage communication with the base station.

The client obtains motor speeds from the base station, and relays them to the
motors. If the received speed for a flipper is zero, it attempts to hold the
position based on encoder data received from the mbed.

The client also obtains the currents going to the motors, as well as total
system voltage and current use, by utilizing current sensors connected via I2C.
In addition, front and rear body pose is returned via I2C-connected IMUs.

All external sensor data is sent back to the base station via UDP.

"""
import logging
import pickle
import socket

from common.exceptions import NoDriversError, MotorCountError, NoSerialsError


class Client(object):
    """
    A client to communicate with the base station and control the robot.

    Parameters
    ----------
    client_address : str
        The local IP address of Yozakura.
    server_address : 2-tuple of (str, int)
        The address at which the server is listening. The elements are the
        server IP address and the port number respectively.

    Attributes
    ----------
    request : socket
        Handles communication with the server.
    server_address : 2-tuple of (str, int)
        The address at which the server is listening. The elements are the
        server IP address and the port number respectively.
    motors : dict
        Contains all registered motors.

        **Dictionary format :** {name (str): motor (Motor)}
    serials : dict
        Contains all registered serial connections.

        **Dictionary format :** {name (str): connection (Serial)}
    current_sensors : dict
        Contains all registered current sensors.

        **Dictionary format :** {name (str): sensor (CurrentSensor)}
    imus : dict
        Contains all registered IMUs.

        **Dictionary format :** {name (str): imu (IMU)}

    """
    def __init__(self, client_address, server_address):
        self._logger = logging.getLogger("{ip}_client"
                                         .format(ip=client_address))
        self._logger.debug("Creating client")
        self.request = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.request.connect(server_address)
        self._logger.info("Connected to {server}:{port}"
                          .format(server=server_address[0],
                                  port=server_address[1]))

        self.request.settimeout(0.5)  # seconds

        self.server_address = server_address
        self._sensors_server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.motors = {}
        self.serials = {}
        self.current_sensors = {}
        self.imus = {}

    def add_serial_device(self, name, ser):
        """
        Register a serial device for ADC communication.

        Parameters
        ----------
        name : str
            The name of the device.
        ser : Serial
            The serial connection to the microcontroller.

        """
        self._logger.debug("Adding {name}".format(name=name))
        self.serials[name] = ser

    def add_motor(self, motor, ser=None, pwm_pins=None):
        """
        Set up and register a motor.

        This method must be called before ``run``. Either ``ser`` or
        ``pwm_pins`` must be provided.

        Parameters
        ----------
        motor : Motor
            The motor to be registered.
        ser : Serial, optional
            The serial connection to communicate with the microcontroller to
            which the motor drivers are connected. This is needed in order to
            enable hardware PWM.
        pwm_pins : 2-tuple of ints, optional
            The pins used for soft PWM. The elements are the PWM pin and the
            DIR pin, respectively.

        Raises
        ------
        NoDriversError
            Neither ``ser`` nor ``pwm_pins`` are provided.

        """
        self._logger.debug("Adding {name}".format(name=motor))
        if not ser and not pwm_pins:
            raise NoDriversError(motor)

        if pwm_pins is not None:
            motor.enable_pwm(*pwm_pins)
        if ser is not None:
            motor.enable_serial(ser)

        self.motors[motor.name] = motor

    def add_current_sensor(self, sensor):
        """
        Register a current sensor.

        Parameters
        ----------
        sensor : CurrentSensor
            The current sensor associated with the motor.

        """
        self._logger.debug("Adding {name}".format(name=sensor))
        self.current_sensors[sensor.name] = sensor

    def add_imu(self, imu):
        """
        Register an IMU.

        Parameters
        ----------
        imu : IMU
            The IMU to be added.

        """
        self._logger.debug("Adding {name}".format(name=imu))
        self.imus[imu.name] = imu

    def run(self):
        """
        Send and handle requests until a ``KeyboardInterrupt`` is received.

        This method connects to the server, and loops forever. It takes the
        speed data from the base station, and manages motor outputs. It
        attempts to hold the flipper position if there is no input.

        If the connection is lost, it shuts down the motors as an emergency
        measure. The motors would continue working if the connection to the
        base station is re-established.

        Raises
        ------
        MotorCountError
            If there are no motors registered
        NoSerialsError
            If there are no serial devices registered

        """
        if not self.motors:
            self._logger.critical("No motors registered!")
            raise MotorCountError(0)

        if not self.serials:
            self._logger.critical("No serial devices registered!")
            raise NoSerialsError

        self._logger.info("Client started")
        timed_out = False

        while True:
            try:
                self.request.send(str.encode("speeds"))  # Request speeds.
                result = self.request.recv(64)  # Receive speed data.
                if not result:
                    self._logger.debug("No speed data")
                    continue
            except BrokenPipeError:
                self._logger.critical("Base station turned off!")
                self._logger.info("Turning off motors")
                for motor in self.motors.values():
                    motor.drive(0)
                raise SystemExit
            except socket.timeout:
                if not timed_out:
                    self._logger.warning("Lost connection to base station")
                    self._logger.info("Turning off motors")
                    for motor in self.motors.values():
                        motor.drive(0)
                    timed_out = True
                continue

            if timed_out:  # Connection returned.
                self._logger.info("Connection returned")
                timed_out = False

            # Get flipper positions from last two items of mbed reply.
            try:
                mbed_data = self.serials["mbed"].readline().split()
                adc_data = [int(i, 16) / 0xFFFF for i in mbed_data]
                lpos, rpos = adc_data[-2:]
            except ValueError:
                self._logger.debug("Bad mbed flipper data")
                adc_data = [0, 0]

            try:
                lwheel, rwheel, lflipper, rflipper = pickle.loads(result)
                self._logger.debug("speeds: {} {} {} {}".format(lwheel, rwheel, lflipper, rflipper))
            except (pickle.UnpicklingError, EOFError):
                self._logger.warning("Bad speed data")
                continue
            self.motors["left_wheel_motor"].drive(lwheel)
            self.motors["right_wheel_motor"].drive(rwheel)

            # TODO(masasin): Hold position if input is 0.
            self.motors["left_flipper_motor"].drive(lflipper)
            self.motors["right_flipper_motor"].drive(rflipper)

            # Get current sensor data to send back.
            current_data = []
            for current_sensor in ("left_motor_current",
                                   "right_motor_current",
                                   "left_flipper_current",
                                   "right_flipper_current",
                                   "motor_current"):
                try:
                    sensor = self.current_sensors[current_sensor]
                except KeyError:
                    current_data.append([0, 0, 0])
                    continue
                current = sensor.get_measurement("current")
                power = sensor.get_measurement("power")
                if current == 0:
                    voltage = 0
                else:
                    voltage = power / current

                current_data.append((current, power, voltage))

            # Get IMU data to send back.
            imu_data = []
            for imu in ("front_imu", "rear_imu"):
                try:
                    rpy = self.imus[imu].rpy
                    imu_data.append(rpy)
                except KeyError:
                    imu_data.append([0, 0, 0])
                    continue

            # Send sensor data back to base station. ROS uses Python 2 for
            # now, so use a maxmium protocol version of 2.
            self._sensors_server.sendto(pickle.dumps((adc_data,
                                                      current_data,
                                                      imu_data),
                                                     protocol=2),
                                        self.server_address)

    def shutdown(self):
        """Shut down the client."""
        self._logger.debug("Shutting down client")
        self.request.close()
        self._logger.info("Client shut down")
