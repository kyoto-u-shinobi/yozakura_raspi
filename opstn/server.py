# (C) 2015  Kyoto University Mechatronics Laboratory
# Released under the GNU General Public License, version 3
"""
Base station server for communicating with Yozakura.

After connecting with the client, the server receives requests, reads input
from a connected controller, and responds accordingly. The server is capable of
being connected to multiple clients simultaneously.

It also contains a UDP server that can be used to read data about flipper
positions, current sensor measurements, and pose information that was sent back
by Yozakura via UDP.

"""
import logging
import pickle
import select
import socket
import socketserver
import time

import numpy as np

from common.exceptions import YozakuraExit


class Handler(socketserver.BaseRequestHandler):
    """
    A handler for connection requests.

    It gets called by the server automatically whenever a new client connects.

    Attributes
    ----------
    request : socket
        Handles communication with the client
    wheels_single_stick : bool
        Whether the wheels are controlled by only the left analog stick.
    reverse_mode : bool
        Whether reverse mode is engaged. In reverse mode, the x- and y- inputs
        are both inverted.

    """
    def __init__(self, request, client_address, server):
        self._logger = logging.getLogger("{client_ip}_handler"
            .format(client_ip=client_address[0]))
        self._logger.debug("New handler created")
        super().__init__(request, client_address, server)
        self.wheels_single_stick = False
        self.reverse_mode = False

    def handle(self):
        """
        Handle the requests to the server.

        Once connected to the client, the handler loops and keeps listening for
        requests. This allows us to find out when the client is disconnected,
        and also allows for a much higher communication rate with the robot
        compared to reopening upon each request.

        Pickle is used on the server and client sides to transfer Python
        objects.

        Requests handled:

        - state : Reply with the state of the controller.
        - inputs : Reply with the raw input data from the state.
        - commands : Perform calculations and send the required motor and arm
          speed data.
        - echo : Reply with what the client has said.
        - print : ``echo``, and print to ``stdout``.

        """
        self._logger.info("Connected to client")
        self.request.settimeout(0.5)  # seconds
        self._sticks_timestamp = self._reverse_timestamp = time.time()

        self._sensors_client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self._sensors_client.setsockopt(socket.SOL_SOCKET,
                                        socket.SO_REUSEADDR, True)
        self._sensors_client.bind(("", 9999))

        try:
            self._loop()
        finally:
            self._sensors_client.close()
            raise YozakuraExit

    def _loop(self):
        """The main handler loop."""
        while True:
            try:
                data = self.request.recv(64).decode().strip()
            except socket.timeout:
                self._logger.warning("Lost connection to robot")
                self._logger.info("Robot has shut down motors")
                continue
            self._logger.debug('Received: "{data}"'.format(data=data))

            if data == "":  # Client exited
                self._logger.info("Terminating client session")
                break

            reply = self._generate_reply(data)

            try:
                self.request.sendall(str.encode(reply))
            except TypeError:  # Already bytecode (e.g., pickled object)
                self.request.sendall(reply)

            # Receive sensor data
            raw_data = self._udp_receive(self, size=1024)
            try:
                flippers, currents, poses, arm_data = pickle.loads(raw_data)
                self._log_sensor_data(flippers, currents, poses, arm_data)
            except (AttributeError, EOFError, IndexError, TypeError) as e:
                self._logger.debug("No or bad data received from robot: {e}"
                                   .format(e=e))
 
    def _generate_reply(self, data):
        """
        Generate the necessary reply given a request string.

        Parameters
        ----------
        data : str
            The request string.

        Returns
        -------
        str or bytes
            The reply to send back to the client.

        """
        if data == "state":
                state = self.server.controllers["main"].state
                reply = pickle.dumps(state.data)
        elif data == "inputs":
            state = self.server.controllers["main"].state
            dpad, lstick, rstick, buttons = state.data
            reply = pickle.dumps(((dpad.x, dpad.y),
                                  (lstick.x, lstick.y),
                                  (rstick.x, rstick.y),
                                  buttons.buttons))
        elif data == "commands":
            state = self.server.controllers["main"].state
            motor_commands, arm_commands = self._generate_commands(state)
            reply = pickle.dumps(motor_commands, arm_commands)
        elif data.split()[0] == "echo":
            reply = " ".join(data.split()[1:])
        elif data.split()[0] == "print":
            reply = " ".join(data.split()[1:])
            self._logger.info('Client says: "{reply}"'
                              .format(reply=reply))
        else:
            reply = 'Unable to parse command: "{cmd}"'.format(cmd=data)
            self._logger.debug(reply)

        return reply

    def _generate_commands(self, state):
        """
        Get required speeds based on controller state and system state.

        Inputs handled:

        - L1, L2 : Rotate left flipper.
        - R1, R2 : Rotate right flipper.
        - lstick : x- and y-axes control wheels in single-stick mode;
          y-axis controls left-side wheels in dual-stick mode.
        - rstick : y-axis controls right-side wheels in dual-stick
          mode.
        - L3 : Toggle the control mode between single and dual sticks.
        - R3 : Toggle reverse mode

        Parameters
        ----------
        state : State
            Represents the controller states.

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

        See also
        --------
        Controller.State

        """
        dpad, lstick, rstick, buttons = state.data

        if buttons.is_pressed("L3"):
            self._switch_control_mode()
        if buttons.is_pressed("R3"):
            self._engage_reverse_mode()

        if self.reverse_mode:
            # Wheels
            if self.wheels_single_stick:
                self._logger.debug("lx: {lx:9.7}  ly: {ly:9.7}"
                                   .format(lx=lstick.x, ly=lstick.y))
                if abs(lstick.y) == 0:  # Rotate in place
                    lwheel = -lstick.x
                    rwheel = lstick.x
                else:
                    l_mult = (1 - lstick.x) / (1 + abs(lstick.x))
                    r_mult = (1 + lstick.x) / (1 + abs(lstick.x))
                    lwheel = lstick.y * l_mult
                    rwheel = lstick.y * r_mult
            else:
                self._logger.debug("ly: {ly:9.7}  ry: {ry:9.7}"
                                   .format(ly=lstick.y, ry=rstick.y))
                lwheel = rstick.y
                rwheel = lstick.y

            # Flippers
            if buttons.all_pressed("L1", "L2"):
                rflipper = 0
            elif buttons.is_pressed("L1"):
                rflipper = 1
            elif buttons.is_pressed("L2"):
                rflipper = -1
            else:
                rflipper = 0

            if buttons.all_pressed("R1", "R2"):
                lflipper = 0
            elif buttons.is_pressed("R1"):
                lflipper = 1
            elif buttons.is_pressed("R2"):
                lflipper = -1
            else:
                lflipper = 0
                
        else:  # Forward mode
            # Wheels
            if self.wheels_single_stick:
                self._logger.debug("lx: {lx:9.7}  ly: {ly:9.7}"
                                   .format(lx=lstick.x, ly=lstick.y))
                if abs(lstick.y) == 0:  # Rotate in place
                    lwheel = lstick.x
                    rwheel = -lstick.x
                else:
                    l_mult = (1 + lstick.x) / (1 + abs(lstick.x))
                    r_mult = (1 - lstick.x) / (1 + abs(lstick.x))
                    lwheel = -lstick.y * l_mult
                    rwheel = -lstick.y * r_mult
            else:
                self._logger.debug("ly: {ly:9.7}  ry: {ry:9.7}"
                                   .format(ly=lstick.y, ry=rstick.y))
                lwheel = -lstick.y
                rwheel = -rstick.y

            # Flippers
            if buttons.all_pressed("L1", "L2"):
                lflipper = 0
            elif buttons.is_pressed("L1"):
                lflipper = 1
            elif buttons.is_pressed("L2"):
                lflipper = -1
            else:
                lflipper = 0

            if buttons.all_pressed("R1", "R2"):
                rflipper = 0
            elif buttons.is_pressed("R1"):
                rflipper = 1
            elif buttons.is_pressed("R2"):
                rflipper = -1
            else:
                rflipper = 0
            
        # Arm
        if buttons.is_pressed("○"):
            linear = dpad.y
        else:
            pitch = dpad.y
            yaw = dpad.x
        
        if buttons.is_pressed("start"):
            mode = 1
        elif buttons.is_pressed("select"):
            mode = 2
        else:
            mode = 0

        motor_commands = [lwheel, rwheel, lflipper, rflipper]
        arm_commands = mode, linear, pitch, yaw
        return motor_commands, arm_commands

    def _switch_control_mode(self):
        """
        Toggle the control mode between single and dual analog sticks.

        Ignores the toggle directive if the mode has been switched within the
        last second.

        """
        current_time = time.time()

        if current_time - self._sticks_timestamp >= 1:
            if self.wheels_single_stick:
                self.wheels_single_stick = False
                self._logger.info("Control mode switched: Use " +
                                  "lstick and rstick to control robot")
            else:
                self.wheels_single_stick = True
                self._logger.info("Control mode switched: Use " +
                                  "lstick to control robot")
            self._sticks_timestamp = current_time

    def _engage_reverse_mode(self):
        """
        Toggle the control mode between forward and reverse.

        In reverse mode, the regular inputs will cause the robot to move
        in reverse as if it were moving forward.

        Ignores the toggle directive if the mode has been switched within the
        last second.

        """
        current_time = time.time()

        if current_time - self._reverse_timestamp >= 1:
            if self.reverse_mode:
                self.reverse_mode = False
                self._logger.info("Reverse mode disabled")
            else:
                self.reverse_mode = True
                self._logger.info("Reverse mode enabled")
            self._reverse_timestamp = current_time

    def _log_sensor_data(self, flippers, currents, poses, arm_data):
        """
        Log sensor data to debug.

        Parameters
        ----------
        flippers : 2-list of floats
            ADC data containing flipper positions, in radians.
        currents : list of 2-list of float
            Current sensor data containing current (A) and voltage (V) values.
        poses : list of 3-list of float
            Pose data containing yaw, pitch, and roll values.
        arm_data : list of lists and float
            The data returned from the arm.

        """
        lwheel, rwheel, lflip, rflip = current_data
        front, rear = np.rad2deg(pose_data)
        arm_pos, servo_vii, (thermo_l, thermo_r), co2_sensor = arm_data

        check = lambda x: "None  " if x is None else "{:6.3f}".format(x)
        check_t = lambda x: "None" if x is None else "{4.1f}".format(x)
        check_c = lambda x: "None  " if x is None else "{:6.1f}".format(x)

        self._logger.debug("lflipper: {lf}  rflipper: {rf}"
                           .format(lf=check(flippers[0]),
                                   rf=check(flippers[1])))
        self._logger.debug("total_iv: {i} A  {v} V"
                           .format(i=check(sum(i[0] for i in current_data)),
                                   v=check(sum(i[1] for i in current_data)/4)))
        self._logger.debug("lwheel_current: {i} A  {v} V"
                           .format(i=check(lwheel[0]), v=check(lwheel[1])))
        self._logger.debug("rwheel_current: {i} A  {v} V"
                           .format(i=check(rwheel[0]), v=check(rwheel[1])))
        self._logger.debug("lflip_current: {i} A  {v} V"
                           .format(i=check(lflip[0]), v=check(lflip[1])))
                           .format(i=lflip[0], v=lflip[1]))
        self._logger.debug("rflip_current: {i} A  {v} V"
                           .format(i=check(rflip[0]), v=check(rflip[1])))
        self._logger.debug("front r: {r}  p: {p}  y: {y}"
                           .format(r=check(front[0]),
                                   p=check(front[1]),
                                   y=check(front[2])))
        self._logger.debug("rear r: {r}  p: {p}  y: {y}"
                           .format(r=check(rear[0]),
                                   p=check(rear[1]),
                                   y=check(rear[2])))
        self._logger.debug("arm linear: {l}  pitch: {p}  yaw: {y}"
                           .format(l=check(arm_pos[0]),
                                   p=check(arm_pos[1]),
                                   y=check(arm_pos[2])))
        self._logger.debug("arm lin_v {l} V  pitch: {p} A  yaw: {y} A"
                           .format(l=check(servo_vii[0]),
                                   p=check(servo_vii[1]),
                                   y=check(servo_vii[2])))
        thermo_l_string = " ".join([check_t(i) for i in thermo_l])
        thermo_r_string = " ".join([check_t(i) for i in thermo_r])
        self._logger.debug("thermo_l: [{l}]".format(thermo_l_string)) 
        self._logger.debug("thermo_r: [{r}]".format(thermo_r_string)) 
        self._logger.debug("co2_sensor: {c}".format(c=check_c(co2_sensor)))
        self._logger.debug(20 * "=")

    def _udp_get_latest(self, size=1, n_bytes=1):
        """
        Get the latest input.

        This function automatically empties the given socket queue.

        Parameters
        ----------
        size : int, optional
            The number of bytes to read at a time.
        n_bytes : int, optional
            The number of bytes to return.

        Returns
        -------
        bytes
            The last received message, or None if the socket was not ready.

        """
        data = []
        input_ready, o, e = select.select([self._server_client],
                                          [], [], 0)  # Check ready.

        while input_ready:
            data.append(input_ready[0].recv(size))  # Read once.
            input_ready, o, e = select.select([self._server_client],
                                              [], [], 0)  # Check ready.

        if not data:
            return None
        elif n_bytes == 1:
            return data[-1]
        else:
            return data[-n_bytes:]

    def _udp_receive(self, size=32):
        """
        Receive UDP data without blocking.

        Parameters
        ----------
        size : int, optional
            The number of bytes to read at a time.

        Returns
        -------
        recv_msg : bytes
            The received message, or None if the buffer was empty.
        """
        recv_msg = None

        try:
            recv_msg = self._udp_get_latest(size)
        except BlockingIOError:
            pass

        return recv_msg


class Server(socketserver.ForkingMixIn, socketserver.TCPServer):
    """
    A forking, logging TCP Server.

    Parameters
    ----------
    server_address : 2-tuple of (str, int)
        The address at which the server is listening. The elements are the
        server address and the port number respectively.
    handler_class : Handler
        The request handler. Each new request generates a separate process
        running that handler.

    Attributes
    ----------
    controllers : dict
        Contains all registered controllers.

        **Dictionary format :** {name (str): controller (Controller)}

    """
    allow_reuse_address = True  # Can resume immediately after shutdown

    def __init__(self, server_address, handler_class):
        self._logger = logging.getLogger("{ip}_server"
                                         .format(ip=server_address[0]))
        self._logger.debug("Creating server")
        super().__init__(server_address, handler_class)
        self._logger.info("Listening to port {port}"
                          .format(port=server_address[1]))
        self.controllers = {}

    def add_controller(self, controller):
        """
        Register a controller.

        Parameters
        ----------
        controller : Controller
            The controller to be registered.

        """
        self._logger.debug("Adding {c} controller".format(c=controller))
        self.controllers[controller.name] = controller

    def remove_controller(self, controller):
        """
        Deregister a controller.

        Parameters
        ----------
        controller : Controller
            The controller to be deregistered.

        """
        self._logger.debug("Removing {c} controller".format(c=controller))
        del self.controllers[controller.name]

    def serve_forever(self, poll_interval=0.5):
        """
        Handle requests until an explicit ``shutdown()`` request.

        Parameters
        ----------
        poll_interval : float, optional
            The polling interval, in seconds.

        """
        self._logger.info("Server started")
        super().serve_forever(poll_interval)
