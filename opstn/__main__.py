# (C) 2015  Kyoto University Mechatronics Laboratory
# Released under the GNU General Public License, version 3
import logging

from common.functions import get_interfaces
from opstn.controller import Controller
from opstn.server import Server, Handler


def main():
    logging.debug("Initializing controllers")
    ip_address = get_interfaces(external=True, active=True)[0].ip
    server = Server((ip_address, 9999), Handler)

    with Controller(0, name="main") as main_controller:
        server.add_controller(main_controller)
        logging.debug("Starting server")
        server.serve_forever()

    logging.info("All done")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
