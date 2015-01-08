# (C) 2015  Kyoto University Mechatronics Laboratory
# Released under the GNU General Public License, version 3
from common.networking import ServerBase, HandlerBase
import pickle


class Handler(HandlerBase):
    def handle(self):
        self.data = self.request.recv(1024).decode().strip()
        self.logger.info('Received: "{}"'.format(self.data))
        if self.data == "body_sticks_y":
            state = self.server.controllers["body"].get_state()
            dpad, lstick, rstick, buttons = state.data
            self.reply = pickle.dumps((lstick.y, rstick.y))
        elif self.data == "body_state":
            state = self.server.controllers["body"].get_state()
            self.reply = pickle.dumps(state)
        elif self.data == "body":
            state = self.server.controllers["body"].get_state()
            dpad, lstick, rstick, buttons = state.data
            self.reply = pickle.dumps(((dpad.x, dpad.y),
                                 (lstick.x, lstick.y),
                                 (rstick.x, rstick.y),
                                 buttons.buttons))
        elif self.data.split()[0] == "echo":
            self.reply = " ".join(self.data.split()[1:])
        else:
            self.reply = 'Unable to parse command: "{}"'.format(self.data)
        try:
            self.request.sendall(str.encode(self.reply))
        except TypeError:  # Already bytecode
            self.request.sendall(self.reply)


class Server(ServerBase):
    def __init__(self, *args):
        super().__init__(*args)
        self.controllers = {}

    def add_controller(self, controller):
        self.logger.debug("Adding controller {}".format(controller))
        self.controllers[controller.name] = controller

    def remove_controller(self, controller):
        del self.controllers[controller.name]
