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
import socket
import socketserver
import time

import numpy as np


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
    reverse mode : bool
        Whether reverse mode is engaged. In reverse mode, the x- and y- inputs
        are both inverted.

    """
    def __init__(self, request, client_address, server):
        self._logger = logging.getLogger("{client_ip}_handler".format(
            client_ip=client_address[0]))
        self._logger.debug("New handler created")
        super().__init__(request, client_address, server)

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
        - speeds : Perform calculations and send the required motor speed
          data.
        - echo : Reply with what the client has said.
        - print : ``echo``, and print to ``stdout``.

        """
        self._logger.info("Connected to client")
        self.request.settimeout(0.5)  # seconds
        self.wheels_single_stick = False
        self.reverse_mode = False
        self._sticks_timestamp = self._reverse_timestamp = time.time()

        # TODO(murata): Remove everything related to _sensors_client and the
        # try/finally block once you add your udp server.
        self._sensors_client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self._sensors_client.setsockopt(socket.SOL_SOCKET,
                                        socket.SO_REUSEADDR, 1)
        self._sensors_client.bind(("", 9999))

        try:
            self._loop()
        finally:
            self._sensors_client.close()
            raise SystemExit

    def _loop(self):
        """The main handler loop."""
        while True:
            try:
                data = self.request.recv(64).decode().strip()
            except socket.timeout:
                self._logger.warning("Lost connection to robot")
                self._logger.info("Robot will shut down motors")
                continue
            self._logger.debug('Received: "{data}"'.format(data=data))
    
            if data == "":  # Client exited safely.
                self._logger.info("Terminating client session")
                break
    
            if data == "state":
                state = self.server.controllers["main"].state
                reply = pickle.dumps(state)
    
            elif data == "inputs":
                state = self.server.controllers["main"].state
                dpad, lstick, rstick, buttons = state
                reply = pickle.dumps(((dpad.x, dpad.y),
                                      (lstick.x, lstick.y),
                                      (rstick.x, rstick.y),
                                      buttons.buttons))
    
            elif data == "speeds":
                state = self.server.controllers["main"].state
                reply = pickle.dumps(self._get_needed_speeds(state))
    
            elif data.split()[0] == "echo":
                reply = " ".join(data.split()[1:])
    
            elif data.split()[0] == "print":
                reply = " ".join(data.split()[1:])
                self._logger.info('Client says: "{reply}"'
                                  .format(reply=reply))
    
            else:
                reply = 'Unable to parse command: "{cmd}"'.format(cmd=data)
                self._logger.debug(reply)
    
            try:
                self.request.sendall(str.encode(reply))
            except TypeError:  # Already bytecode
                self.request.sendall(reply)
    
            # Receive sensor data
            raw_data, address = self._sensors_client.recvfrom(1024)
            try:
                adc_data, current_data, pose_data = pickle.loads(raw_data)
                self._log_sensor_data(adc_data, current_data, pose_data)
            except (AttributeError, EOFError, IndexError, TypeError):
                self._logger.debug("No or bad data received from robot")

    def _get_needed_speeds(self, state):
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
        state : tuple
            Represents the controller states.

        Returns
        -------
        float
            The speed inputs for each of the four motors, with values
            between -1 and 1. The four motors are:

            - Left wheel
            - Right wheel
            - Left flipper
            - Right flipper

        See also
        --------
        Controller.State

        """
        # TODO(masasin): Handle select : Synchronize flipper positions.
        # TODO(masasin): Handle start : Move flippers to forward position.
        dpad, lstick, rstick, buttons = state

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

        return lwheel, rwheel, lflipper, rflipper

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

    def _log_sensor_data(self, adc_data, current_data, pose_data):
        """
        Log sensor data to debug.

        Parameters
        ----------
        adc_data : 2-list of floats
            ADC data containing flipper positions, in radians.
        current_data : 3-list of 3-list of floats
            Current sensor data containing current, power, and voltage values.
        pose_data : 2-list of 3-list of floats
            Pose data containing yaw, pitch, and roll values.

        """
        lwheel, rwheel, lflip, rflip, battery = current_data
        front, rear = np.rad2deg(pose_data)

        self._logger.debug("lflipper: {lf:6.3f}  rflipper: {rf:6.3f}"
                           .format(lf=adc_data[0], rf=adc_data[1]))
        self._logger.debug("lwheel_current: {i:6.3f} A  {p:6.3f} W  {v:6.3f} V"
                           .format(i=lwheel[0], p=lwheel[1], v=lwheel[2]))
        self._logger.debug("rwheel_current: {i:6.3f} A  {p:6.3f} W  {v:6.3f} V"
                           .format(i=rwheel[0], p=rwheel[1], v=rwheel[2]))
        self._logger.debug("lflip_current: {i:6.3f} A  {p:6.3f} W  {v:6.3f} V"
                           .format(i=lflip[0], p=lflip[1], v=lflip[2]))
        self._logger.debug("rflip_current: {i:6.3f} A  {p:6.3f} W  {v:6.3f} V"
                           .format(i=rflip[0], p=rflip[1], v=rflip[2]))
        self._logger.debug("batt_current: {i:6.3f} A  {p:6.3f} W  {v:6.3f} V"
                           .format(i=battery[0], p=battery[1], v=battery[2]))
        self._logger.debug("front r: {r:6.3f}  p: {p:6.3f}  y: {y:6.3f}"
                           .format(r=front[0], p=front[1], y=front[2]))
        self._logger.debug("rear r: {r:6.3f}  p: {p:6.3f}  y: {y:6.3f}"
                           .format(r=rear[0], p=rear[1], y=rear[2]))
        self._logger.debug(20 * "=")


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
        self._logger.debug("Adding {c} controller".format(cs=controller))
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
