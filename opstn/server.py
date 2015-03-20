# (C) 2015  Kyoto University Mechatronics Laboratory
# Released under the GNU General Public License, version 3
"""
Server for Kaginawa motor commands.

After connecting with the client, the server receives requests and responds
accordingly. Can read joystick input, and connect to multiple clients
simultaneously.

"""
import pickle
import multiprocessing as mp
from socket import timeout
import time

from common.networking import TCPServerBase, TCPHandlerBase
from opstn.client import Client


class Handler(TCPHandlerBase):
    """A handler for connection requests.

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
    def handle(self):
        """
        Handle the requests to the server.

        Once connected to the client, the handler loops and keeps listening for
        requests. This allows us to find out when the client is disconnected,
        and also allows for a much higher communication rate with the robot.

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
        self.logger.info("Connected to client")
        self.request.settimeout(0.5)  # seconds
        self.wheels_single_stick = False
        self.reverse_mode = False
        self._sticks_timestamp = self._reverse_timestamp = time.time()
        
        client = Client((self.client_address[0], 9999))
        client_process = mp.Process(target=client.run)
        client_process.start()
        
        try:
            while True:
                try:
                    data = self.receive(64).decode().strip()
                except timeout:
                    self.logger.warning("Lost connection to robot")
                    self.logger.info("Robot will shut down motors")
                    continue
                self.logger.debug('Received: "{}"'.format(data))
    
                if data == "":  # Client exited safely.
                    self.logger.info("Terminating client session")
                    break
    
                if data == "state":
                    state = self.server.controllers["main"].get_state()
                    reply = pickle.dumps(state)
    
                elif data == "inputs":
                    state = self.server.controllers["main"].get_state()
                    dpad, lstick, rstick, buttons = state.data
                    reply = pickle.dumps(((dpad.x, dpad.y),
                                          (lstick.x, lstick.y),
                                          (rstick.x, rstick.y),
                                          buttons.buttons))
    
                elif data == "speeds":
                    state = self.server.controllers["main"].get_state()
                    reply = pickle.dumps(self._get_needed_speeds(state))
    
                elif data.split()[0] == "echo":
                    reply = " ".join(data.split()[1:])
    
                elif data.split()[0] == "print":
                    reply = " ".join(data.split()[1:])
                    self.logger.info('Client says: "{}"'.format(reply))
    
                else:
                    reply = 'Unable to parse command: "{}"'.format(data)
                    self.logger.debug(reply)
    
                self.send(reply)
        finally:
            client_process.terminate()

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
        state : State
            Represents the controller states.

        Returns
        -------
        float
            The speed inputs for each of the four motors, with values
            between -1 and 1. The four motors are:
                - Left motor
                - Right motor
                - Left flipper
                - Right flipper

        """
        # TODO(masasin): Handle select : Synchronize flipper positions.
        # TODO(masasin): Handle start : Move flippers to forward position.
        dpad, lstick, rstick, buttons = state.data

        if buttons.is_pressed("L3"):
            self._switch_control_mode()
        if buttons.is_pressed("R3"):
            self._engage_reverse_mode()

        if self.reverse_mode:
            # Wheels
            if self.wheels_single_stick:
                self.logger.debug("lx: {:9.7}  ".fromat(lstick.x) +
                                  "ly: {:9.7}".format(lstick.y))
                if abs(lstick.y) == 0:  # Rotate in place
                    lmotor = -lstick.x
                    rmotor = lstick.x
                else:
                    l_mult = (1 - lstick.x) / (1 + abs(lstick.x))
                    r_mult = (1 + lstick.x) / (1 + abs(lstick.x))
                    lmotor = lstick.y * l_mult
                    rmotor = lstick.y * r_mult
            else:
                self.logger.debug("ly: {:9.7}  ".fromat(lstick.y) +
                                  "ry: {:9.7}".format(rstick.y))
                lmotor = rstick.y
                rmotor = lstick.y

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
                self.logger.debug("lx: {:9.7}  ".format(lstick.x) +
                                  "ly: {:9.7}".format(lstick.y))
                if abs(lstick.y) == 0:  # Rotate in place
                    lmotor = lstick.x
                    rmotor = -lstick.x
                else:
                    l_mult = (1 + lstick.x) / (1 + abs(lstick.x))
                    r_mult = (1 - lstick.x) / (1 + abs(lstick.x))
                    lmotor = -lstick.y * l_mult
                    rmotor = -lstick.y * r_mult
            else:
                self.logger.debug("ly: {:9.7}  ".format(lstick.y) +
                                  "ry: {:9.7}".format(rstick.y))
                lmotor = -lstick.y
                rmotor = -rstick.y

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

        return lmotor, rmotor, lflipper, rflipper

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
                self.logger.info("Control mode switched: Use " +
                                 "lstick and rstick to control robot")
            else:
                self.wheels_single_stick = True
                self.logger.info("Control mode switched: Use " +
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
                self.logger.info("Reverse mode disabled!")
            else:
                self.reverse_mode = True
                self.logger.info("Reverse mode enabled!")
            self._reverse_timestamp = current_time


class Server(TCPServerBase):
    """
    A TCP Server.

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
        Contains all registered motors.

        **Dictionary format :** {name (str): controller (Controller)}

    """
    def __init__(self, server_address, handler_class):
        super().__init__(server_address, handler_class)
        self.controllers = {}

    def add_controller(self, controller):
        """
        Register a controller.

        Parameters
        ----------
        controller : Controller
            The controller to be registered.

        """
        self.logger.debug("Adding controller {}".format(controller))
        self.controllers[controller.name] = controller

    def remove_controller(self, controller):
        """Deregister a controller.

        Parameters
        ----------
        controller : Controller
            The controller to be deregistered.
        """
        self.logger.debug("Removing controller {}".format(controller))
        del self.controllers[controller.name]
