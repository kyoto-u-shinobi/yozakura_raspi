# (C) 2015  Kyoto University Mechatronics Laboratory
# Released under the GNU General Public License, version 3
from common.networking import ServerBase, HandlerBase
import pickle
import socket


class Handler(HandlerBase):
    """A handler for connection requests.

    Attributes:
        request: A socket object handling communication with the client.
    """
    def handle(self):
        """Handle the requests.

        Once connected to the client, the handler loops and keeps listening for
        input. This allows us to find out when the client is disconnected, and
        also allows for a much higher communication rate with the robot.

        Inputs handled:
            state: Reply with the state of the controller.
            echo: Reply with what the client has said.
            print: Reply with what the client has said, and print to screen.
        """
        self.logger.info("Connected to client")
        self.request.settimeout(0.5)

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


class Server(ServerBase):
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
