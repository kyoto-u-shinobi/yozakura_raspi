# (C) 2015  Kyoto University Mechatronics Laboratory
# Released under the GNU General Public License, version 3
from common.networking import Server, Handler
from common import joystick
import logging
import pickle


class OpstnHandler(Handler):
    def handle(self):
        self.data = self.request.recv(1024).decode().strip()
        self.logger.info("{}".format(self.data))
        if self.data == "sticks_y":
            state = stick_body.get_state()
            dpad, lstick, rstick, buttons = state.data
            reply = pickle.dumps((lstick.y, rstick.y))
        elif self.data == "state":
            state = stick_body.get_state()
            reply = pickle.dumps(state)
        elif self.data == "body":
            state = stick_body.get_state()
            dpad, lstick, rstick, buttons = state.data
            reply = pickle.dumps(((dpad.x, dpad.y),
                                 (lstick.x, lstick.y),
                                 (rstick.x, rstick.y),
                                 buttons.buttons))
        else:
            reply = 'Unable to parse command: "{}"'.format(self.data)
        try:
            self.request.sendall(str.encode(reply))
        except TypeError:  # Already bytecode
            self.request.sendall(reply)

if __name__=="__main__":
    logging.basicConfig(level=logging.INFO)
    server = Server(("localhost", 9999), OpstnHandler)
    stick_body = joystick.Controller(0)

    try:
        server.serve_forever()
    finally:
        logging.info("Shutting down...")
        joystick.Controller.quit_all()
    logging.info("All done")
