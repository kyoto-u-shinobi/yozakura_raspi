# (C) 2015  Kyoto University Mechatronics Laboratory
# Released under the GNU General Public License, version 3
from opstn.server import Server, Handler
from common import networking, joystick
import logging

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    try:
        ip_address = networking.get_ip_address("eth0")
    except OSError:
        ip_address = networking.get_ip_address("enp2s0")
    server = Server((ip_address, 9999), Handler)

    logging.debug("Initializing controllers")
    stick_body = joystick.Controller(0, name="body")
    server.add_controller(stick_body)

    try:
        logging.debug("Starting server")
        server.serve_forever()
    finally:
        logging.info("Shutting down...")
        joystick.Controller.quit_all()
    logging.info("All done")
