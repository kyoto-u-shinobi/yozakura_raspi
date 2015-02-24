# (C) 2015  Kyoto University Mechatronics Laboratory
# Released under the GNU General Public License, version 3
import pickle
import socket

from ..common.networking import TCPServerBase, HandlerBase


class Handler(HandlerBase):
    """A handler for connection requests.

    Attributes:
        request: A socket object handling communication with the client.
        wheels_single_stick: A boolean indicating whether the wheels are
            controlled by only one stick (i.e., the left analog stick).
        reverse_mode: A boolean indicating whether reverse mode is engaged.
            With reverse mode, the inputs are inverted for ease of operation.
    """
    def handle(self):
        """Handle the requests.

        Once connected to the client, the handler loops and keeps listening for
        input. This allows us to find out when the client is disconnected, and
        also allows for a much higher communication rate with the robot.

        Inputs handled:
            state: Reply with the state of the controller.
            inputs: Reply with the raw input data from the state.
            speeds: Perform calculations and send motor speed data.
            echo: Reply with what the client has said.
            print: Reply with what the client has said, and print to screen.
        """
        self.logger.info("Connected to client")
        self.request.settimeout(0.5)
        self.wheels_single_stick = False
        self.reverse_mode = False
        
        self._sticks_timestamp = self._reverse_timestamp = time.time()

        while True:
            try:
                data = self.request.recv(1024).decode().strip()
            except socket.timeout:
                self.logger.warning("Lost connection to robot")
                self.logger.info("Robot will shut down motors")
                continue
            self.logger.debug('Received: "{}"'.format(data))

            if data == "":  # Client exited safely.
                self.logger.info("Terminating client session")
                break

            if data == "state":
                state = self.server.controllers["wheels"].get_state()
                reply = pickle.dumps(state)
            elif data == "inputs":
                state = self.server.controllers["wheels"].get_state()
                dpad, lstick, rstick, buttons = state.data
                self.reply = pickle.dumps(((dpad.x, dpad.y),		
                                           (lstick.x, lstick.y),		
                                           (rstick.x, rstick.y),		
                                           buttons.buttons))
            elif data == "speeds":
                state = self.server.controllers["wheels"].get_state()
                self.reply = pickle.dumps(self._handle_inputs, state)
            elif data.split()[0] == "echo":
                reply = " ".join(data.split()[1:])
            elif data.split()[0] == "print":
                reply = " ".join(data.split()[1:])
                self.logger.info('Client says: "{}"'.format(reply))
            else:
                reply = 'Unable to parse command: "{}"'.format(data)
                self.logger.debug(reply)

            try:
                self.request.sendall(str.encode(reply))
            except TypeError:  # Already bytecode
                self.request.sendall(reply)

        def _handle_input(self, state):
        """Handle input from the joystick.

        Inputs handled:
            L1: Rotate left flipper upwards from start.
            L2: Rotate left flipper downwards from start.
            R1: Rotate right flipper upwards from start.
            R2: Rotate right flipper downwards from start.
            lstick: x- and y- axes control wheels in single-stick mode;
                    y-axis controls left-side wheels in dual-stick mode.
            rstick: y-axis controls right-side wheels in dual-stick mode.
            L3: Toggle the control mode between single and dual analog sticks.
            R3: Toggle reverse mode

        TODO (masasin):
            Handle select: Synchronize flipper positions.
            Handle start: Move flippers to a horizontal and forward position.

        Args:
            state: A state object representing the controller state.

        Returns:
            The speed inputs for each of the four motors:
                Left motor speed
                Right motor speed
                Left flipper speed
                Right flipper speed
        """
        dpad, lstick, rstick, buttons = state.data

        if buttons.buttons[10]:  # The L3 button was pressed
            self._switch_control_mode()
        if buttons.buttons[11]:  # The R3 button was pressed
            self._engage_reverse_mode()

        if self.reverse_mode:
            # Flippers
            if buttons.buttons[4]:  # L1
                rflipper = 1
            elif buttons.buttons[6]:  # L2
                rflipper = -1
            else:
                rflipper = 0

            if buttons.buttons[5]:  # R1
                lflipper = 1
            elif buttons.buttons[7]:  # R2
                lflipper = -1
            else:
                lflipper = 0

        else:  # Forward mode
            # Wheels
            if self.wheels_single_stick:
                self.logger.debug("lx: {:9.7}  ly: {:9.7}".format(lstick.x,
                                                                  lstick.y))
                if abs(lstick.y) < 0.1:  # Rotate in place
                    lmotor = lstick.x
                    rmotor = -lstick.x
                else:
                    l_mult = (1 + lstick.x) / (1 + abs(lstick.x))
                    r_mult = (1 - lstick.x) / (1 + abs(lstick.x))
                    lmotor = -lstick.y * l_mult
                    rmotor = -lstick.y * r_mult
            else:
                self.logger.debug("ly: {:9.7}  ry: {:9.7}".format(lstick.y,
                                                                  rstick.y))
                lmotor = -lstick.y
                rmotor = -rstick.y

            # Flippers
            if buttons.buttons[4]:  # L1
                lflipper = 1
            elif buttons.buttons[6]:  # L2
                lflipper = -1
            else:
                lflipper = 0
            
            if buttons.buttons[5]:  # R1
                rflipper = 1
            elif buttons.buttons[7]:  # R2
                rflipper = -1
            else:
                rflipper = 0

        return lmotor, rmotor, lflipper, rflipper

    def _switch_control_mode(self):
        """Toggle the control mode between single and dual analog sticks.

        Ignores the toggle directive if the mode has been switched within the
        last second.
        """
        current_time = time.time()

        if current_time - self._sticks_timestamp >= 1:
            if self.wheels_single_stick:
                self.wheels_single_stick = False
                self.logger.info("Control mode switched: Use " +\
                                 "lstick and rstick to control robot")
            else:
                self.wheels_single_stick = True
                self.logger.info("Control mode switched: Use " +\
                                 "lstick to control robot")
            self._sticks_timestamp = current_time
            
    def _engage_reverse_mode(self):
        """Toggle the control mode between forward and reverse.
        
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
    """A TCP Server"""
    def __init__(self, *args, **kwargs):
        """Inits the server."""
        super().__init__(*args, **kwargs)
        self.controllers = {}

    def add_controller(self, controller):
        """Register a controller.

        Args:
            controller: The controller to be registered.
        """
        self.logger.debug("Adding controller {}".format(controller))
        self.controllers[controller.name] = controller

    def remove_controller(self, controller):
        """Deregister a controller.

        Args:
            controller: The controller to be deregistered.
        """
        self.logger.debug("Removing controller {}".format(controller))
        del self.controllers[controller.name]
