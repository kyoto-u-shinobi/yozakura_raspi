# (C) 2015  Kyoto University Mechatronics Laboratory
# Released under the GNU General Public License, version 3
import logging

import pygame

from common.exceptions import NoControllerError
from common.functions import get_ip_address
from opstn.controller import Controller
from opstn.server import Server, Handler


def main():
    logging.debug("Initializing controllers")
    try:
        stick_body = Controller(0, name="main")
    except pygame.error:
        raise NoControllerError

    try:
        ip_address = get_ip_address(["eth0", "enp2s0", "wlan0"])
        server = Server((ip_address, 9999), Handler)
        server.add_controller(stick_body)
        logging.debug("Starting server")
        server.serve_forever()
    finally:
        logging.info("Shutting down...")
        Controller.shutdown_all()
    logging.info("All done")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
