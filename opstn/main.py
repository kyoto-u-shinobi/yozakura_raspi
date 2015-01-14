# (C) 2015  Kyoto University Mechatronics Laboratory
# Released under the GNU General Public License, version 3
from opstn.server import Server, Handler
from common import networking, controller
import logging

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    try:
        ip_address = networking.get_ip_address("eth0")
    except OSError:
        ip_address = networking.get_ip_address("enp2s0")
    server = Server((ip_address, 9999), Handler)

    logging.debug("Initializing controllers")
    stick_body = controller.Controller(0, name="wheels")
    server.add_controller(stick_body)

    try:
        logging.debug("Starting server")
        server.serve_forever()
    finally:
        logging.info("Shutting down...")
        controller.Controller.shutdown_all()
    logging.info("All done")
