# (C) 2015  Kyoto University Mechatronics Laboratory
# Released under the GNU General Public License, version 3
"""
Communicate with the base station and run the robot.

The client obtains motor speeds and arm commands from the base station, and
relays them to the respective mbed.

If the received speed for a flipper is zero, it attempts to hold the position
based on potentiometer data received from the body mbed. It also does not allow
the flipper to move beyond the capabilities of the potentiometer.

The client also obtains the currents going to individual motors from current
sensors connected via I2C. In addition, front and rear body pose are returned
via two I2C-connected IMUs.

From the arm mbed, the client receives servo positions, voltages, and currents;
two 4x4 temperature matrices; and readings from a |CO2| sensor attached to the
arm.

All external sensor data is sent back to the base station asynchronously via
UDP.

"""
from collections import OrderedDict
import logging
import pickle
import socket

from common.exceptions import BadDataError, YozakuraTimeoutError,\
    NoConnectionError, NoMbedError, MotorCountError, NoDriversError
from rpi.motor import Motor
from rpi.bitfields import ArmPacket


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

    Raises
    ------
    NoConnectionError
        The client cannot connect to the base station.

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
    mbeds : dict
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
        try:
            self.request.connect(server_address)
        except ConnectionRefusedError:
            raise NoConnectionError("Base station is not connected! " +
                                    "Is the server on?")
        except OSError:
            raise NoConnectionError("Base station is on the wrong network! " +
                                    "Is its IP address is static?")
        self._logger.info("Connected to {server}:{port}"
                          .format(server=server_address[0],
                                  port=server_address[1]))

        self.request.settimeout(0.5)  # seconds

        self.server_address = server_address
        self._sensors_server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.motors = OrderedDict()
        self.mbeds = {}
        self.current_sensors = {}
        self.imus = {}

        self._timed_out = False

    def add_mbed(self, name, ser):
        """
        Register an mbed.

        Parameters
        ----------
        name : str
            The name of the device.
        ser : Mbed
            The serial connection to the mbed.

        """
        self._logger.debug("Adding {name}".format(name=name))
        self.mbeds[name] = ser

    def add_motor(self, motor, ser=None, pwm_pins=None):
        """
        Set up and register a motor.

        This method must be called before `run`. Either `ser` or
        `pwm_pins` must be provided.

        Parameters
        ----------
        motor : Motor
            The motor to be registered.
        ser : Serial, optional
            The serial connection to communicate with the mbed to which the
            motor drivers are connected. This is needed in order to enable
            hardware PWM.
        pwm_pins : 2-tuple of ints, optional
            The pins used for soft PWM. The elements are the PWM pin and the
            DIR pin, respectively.

        Raises
        ------
        NoDriversError
            Neither `ser` nor `pwm_pins` have been provided.

        """
        self._logger.debug("Adding {name}".format(name=motor))
        if not ser and not pwm_pins:
            raise NoDriversError(motor)

        if pwm_pins is not None:
            motor.enable_soft_pwm(*pwm_pins)
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
        try:
            self._logger.debug("Adding {name}".format(name=sensor))
        except AttributeError:
            return
        self.current_sensors[sensor.name] = sensor

    def add_imu(self, imu):
        """
        Register an IMU.

        Parameters
        ----------
        imu : IMU
            The IMU to be added.

        """
        try:
            self._logger.debug("Adding {name}".format(name=imu))
        except AttributeError:
            return
        self.imus[imu.name] = imu

    def run(self):
        """
        Send and handle requests until a `KeyboardInterrupt` is received.

        This method connects to the server, and loops forever. It takes the
        speed and arm commands from the base station, and manages the outputs.
        It attempts to hold the flipper position if there is no input.

        If the connection is lost, it shuts down the motors as an emergency
        measure. The motors would continue working if the connection to the
        base station is re-established.

        Raises
        ------
        MotorCountError
            There are fewer than four motors registered.
        NoMbedError
            The body mbed is not registered, or no mbeds are registered.

        """
        if len(self.motors) < 4:
            self._logger.critical("Insufficient motors registered!")
            raise MotorCountError(len(self.motors))

        if len(self.mbeds) == 0:
            raise NoMbedError("No mbeds are registered.")

        if "mbed_body" not in self.mbeds:
            raise NoMbedError("The body mbed is not registered.")

        self._logger.info("Client started")

        while True:
            try:
                motor_commands, arm_commands = self._request_commands()
            except BadDataError as e:
                self._logger.debug(e)
                continue
            except socket.timeout:
                if not self._timed_out:
                    self._handle_timeout()
                continue
            except BrokenPipeError:
                self._logger.critical("Base station turned off!")
                raise NoConnectionError("Base station turned off!")
            else:
                self._logger.debug("Received speeds")

            if self._timed_out:
                self._logger.info("Connection returned")
                self._timed_out = False

            flipper_positions = self._get_flipper_positions()
            self._drive_motors(motor_commands, flipper_positions)
            self._command_arm(arm_commands)

            current_data = self._get_current_data("left_wheel_current",
                                                  "right_wheel_current",
                                                  "left_flipper_current",
                                                  "right_flipper_current")
            imu_data = self._get_imu_data("front_imu", "rear_imu")
            arm_data = self._get_arm_data()

            self._send_data(flipper_positions, current_data, imu_data, arm_data)

    def _handle_timeout(self):
        """Turn off motors in case of a lost connection."""
        self._logger.warning("Lost connection to base station")
        self._logger.info("Turning off motors")
        Motor.shutdown_all()
        self._timed_out = True

    def _request_commands(self):
        """
        Request speed data from base station.

        Returns
        -------
        motor_commands : 4-list of float
            A list of the speeds requested of each motor:

            - Left wheel motor
            - Right wheel motor
            - Left flipper motor
            - Right flipper motor

        arm_commands : 4-tuple of int
            A list of commands for the arm servos:

            - mode
            - linear
            - pitch
            - yaw

        """
        self._logger.debug("Requesting commands")
        # TODO (murata): Change "speeds" to "commands" in opstn.
        self.request.send("commands".encode())
        result = self.request.recv(128)
        if not result:
            raise BadDataError("No motor or arm commands received")

        try:
            motor_commands, arm_commands = pickle.loads(result)
        except (pickle.UnpicklingError, EOFError) as e:
            raise BadDataError("Invalid motor or arm commands received: {e}"
                               .format(e=e))

        return motor_commands, arm_commands

    def _drive_motors(self, motor_commands, positions):
        """
        Drive all the motors.

        Parameters
        ----------
        motor_commands : 4-list of float
            The speeds with which to drive the four motors.

        """
        self._logger.debug("Driving motors")
        # Stop when approaching potentiometer limits.
        if positions[0] is not None and not 0.05 < positions[0] < 0.95:
            if positions[0] <= 0.05 and motor_commands[2] == -1:
                self._logger.warning("Left flipper near limit: {pos:5.3f}"
                                     .format(pos=positions[0]))
        if positions[0] is not None\
            and ((positions[0] <= 0.05 and motor_commands[2] == -1) or
                 (positions[0] >= 0.95 and motor_commands[2] == 1)):
            self._logger.warning("Left flipper is near its limit: {pos:5.3f}"
                                 .format(pos=positions[0]))
            motor_commands[2] = 0
        if positions[1] is not None\
            and ((positions[1] <= 0.05 and motor_commands[3] == 1) or
                 (positions[1] >= 0.95 and motor_commands[3] == -1)):
            self._logger.warning("Right flipper is near its limit: {pos:5.3f}"
                                 .format(pos=positions[1]))
            motor_commands[3] = 0

        for motor, speed in zip(self.motors.values(), motor_commands):
            motor.drive(speed)

    def _command_arm(self, commands):
        """
        Command the arm.

        Yozakura is capable of running without the arm connected. If the arm is
        not connected, do not do anything.

        Parameters
        ----------
        commands : 4-tuple of int
            A list of commands for the arm servos.

        """
        self._logger.debug("Commanding arm")
        if "mbed_arm" in self.mbeds:
            mode, linear, pitch, yaw = [2 if i == -1 else i for i in commands]
            packet = ArmPacket()
            packet.mode = mode
            packet.linear = int(linear)
            packet.pitch = int(pitch)
            packet.yaw = int(yaw)

            self.mbeds["mbed_arm"].write(bytes([packet.as_byte]))

    def _get_flipper_positions(self):
        """
        Get the flipper positions from the body mbed.

        The body mbed has six Analog-to-Digital Conversion ports, to which
        potentiometers attached to the flippers are connected.

        The positions range from 0 to 1, and represent ten revolutions of the
        potentiometer.

        The potentiometers used are XXX. [#]_

        .. warning:: The left and right flipper change the potentiometer
                     position in opposite directions for a given change in angle
                     relative to the body of the robot.

        Returns
        -------
        positions : 2-tuple of float
            The flipper position data from the mbed, or ``[None, None]`` if
            invalid data was obtained. The items are:

            - Left flipper position.
            - Right flipper position.

        References
        ----------
        .. [#] XXX The potentiometer

        """
        # TODO (masasin): What is the potentiometer used?
        self._logger.debug("Requesting mbed body data")
        try:
            mbed_body_data = self.mbeds["mbed_body"].data
            positions = [int(i, 16) / 0xFFFF for i in mbed_body_data]
        except (IndexError, ValueError, YozakuraTimeoutError):
            self._logger.debug("Bad mbed flipper data")
            positions = [None, None]
        else:
            self._logger.debug("Received mbed body data")

        self._logger.verbose("Flipper positions: {pos}".format(pos=positions))

        return positions

    def _get_arm_data(self, ignore=False):
        """
        Get transmitted data from the arm mbed.

        The arm mbed is connected to the servos driving the arm, as well as
        to two temperature sensors and a CO2 sensor.

        If bad data is received, or if the mbed is not connected, every value
        returned will be ``None``.

        Parameters
        ----------
        ignore : bool, optional
            Whether to return empty data without querying the mbed.

        Returns
        -------
        positions : 3-list of float
            The positions of the linear, pitch, and yaw servos respectively.
        servo_vii : 3-list of float
            The voltage reading of the linear servo in volts, and the current
            readings of the pitch and yaw servos in milliamperes.
        thermo_sensors : 2-list of 16-list of float
            The temperature matrices of the left and right 4x4 thermal sensors
            respectively. Units are in degrees Celsius.
        co2_sensor : float
            The reading of the carbon dioxide sensor in PPM.

        """
        self._logger.debug("Requesting arm data")
        if ignore:
            float_arm_data = [None] * 39
        else:
            if "mbed_arm" in self.mbeds:
                self._logger.debug("mbed connected")
                try:
                    mbed_arm_data = self.mbeds["mbed_arm"].data
                    if len(mbed_arm_data) != 39:
                        raise IndexError("Too few items received")
                    float_arm_data = [float(i) for i in mbed_arm_data]
                except (IndexError, ValueError, YozakuraTimeoutError) as e:
                    self._logger.debug("Bad mbed sensor data: {e}".format(e=e))
                    float_arm_data = [None] * 39
            else:
                self._logger.debug("Arm mbed not in mbeds")
                float_arm_data = [None] * 39

        positions = [None if i == -1 else i for i in float_arm_data[0:3]]
        servo_vii = [None if i == -1 else i for i in float_arm_data[3:6]]

        thermo_l = float_arm_data[6:22]
        thermo_r = float_arm_data[22:38]
        thermo_sensors = [thermo_l, thermo_r]

        co2_sensor = float_arm_data[38]

        self._logger.verbose("Servo positions: {pos}".format(pos=positions))
        self._logger.verbose("Servo VII: {vii}".format(vii=servo_vii))
        self._logger.verbose("Left temperature: {tl}".format(tl=thermo_l))
        self._logger.verbose("Right temperature: {tr}".format(tr=thermo_r))
        self._logger.verbose("CO2: {ppm} PPM".format(ppm=co2_sensor))

        return positions, servo_vii, thermo_sensors, co2_sensor

    def _get_current_data(self, *current_sensors):
        """
        Get data from the requested current sensors.

        Parameters
        ----------
        current_sensors : list of str
            A list containing the names of the current sensors to be read.

        Returns
        -------
        current_data : list of 2-list of float
            A list containing the current (A) and voltage (V) readings of each
            sensor. If invalid sensor data was obtained, the readings are set to
            ``[None, None, None]`` by default.

        """
        self._logger.debug("Requesting current data")
        current_data = []
        for sensor in current_sensors:
            try:
                current_data.append(self.current_sensors[sensor].iv)
            except (KeyError, OSError) as e:
                self._logger.debug("Bad current sensor data: {e}".format(e=e))
                current_data.append([None, None])
        return current_data

    def _get_imu_data(self, *imus):
        """
        Get data from the requested inertial measurement units.

        Parameters
        ----------
        imus : list of str
            A list containing the names of the IMUs to be read.

        Returns
        -------
        imu_data : list of 3-list of float
            A list containing the roll, pitch, and yaw readings of each sensor,
            in radians. If invalid sensor data was obtained, the readings are
            set to ``[None, None, None]`` by default.

        """
        self._logger.debug("Getting imu data")
        imu_data = []
        for imu in imus:
            try:
                imu_data.append(self.imus[imu].rpy)
            except (KeyError, OSError) as e:
                self._logger.debug("Bad IMU data: {e}".format(e=e))
                imu_data.append([None, None, None])

        self._logger.verbose("Front IMU data: {}".format(imu_data[0]))
        self._logger.verbose(" Rear IMU data: {}".format(imu_data[1]))
        self._logger.debug("Got imu data")
        return imu_data

    def _send_data(self, flipper_positions, current_data, imu_data, arm_data,
                   protocol=2):
        """
        Send data to base station.

        This method sends data via UDP. UDP is asynchronous, and allows the base
        station to work at a different rate than the robot, and ignore old data.

        Parameters
        ----------
        flipper_positions : 2-list of float
            The positions of the flippers.
        current_data : list of 2-list of float
            The current sensor measurements.
        imus : list of 3-list of float
            The IMU measurements.
        arm_data : list of lists and float
            The data returned from the arm.
        protocol : int, optional
            The protocol to use to pickle the data. The ROS-based base station
            software uses Python 2, and therefore the maximum usable protocol
            version is 2. If you are sure that Python 2 will not be
            used, feel free to use whatever protocol you want.

        See Also
        --------
        _get_arm_data

        """
        self._logger.debug("Sending data to base station")
        self._sensors_server.sendto(pickle.dumps((flipper_positions,
                                                  current_data,
                                                  imu_data,
                                                  arm_data),
                                                 protocol=protocol),
                                    self.server_address)

    def _read_last_line(self, ser):
        """
        Read the last line from a serial device's buffer.

        Parameters
        ----------
        ser : str
            The name of the serial device to be read.

        Returns
        -------
        str
            The last line from the serial device's buffer.

        """
        buffer_string = ""
        dev = self.mbeds[ser]
        while True:
            buffer_string += dev.read(dev.inWaiting()).decode()
            if "\n" in buffer_string:
                lines = buffer_string.split("\n")
                return lines[-2]

    def shutdown(self):
        """Shut down the client."""
        Motor.shutdown_all()
        self._logger.debug("Shutting down connections with mbeds")
        for mbed in self.mbeds:
            mbed.close()
        self._logger.debug("Shutting down client")
        self.request.close()
        self._logger.info("Client shut down")
