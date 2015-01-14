# (C) 2015  Kyoto University Mechatronics Laboratory
# Released under the GNU General Public License, version 3
from opstn.server import Server, Handler
from common import networking, joystick
import logging

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    stick_body = joystick.Controller(0, name="body")

    try:
        ip_address = networking.get_ip_address("eth0")
    except OSError:
        ip_address = networking.get_ip_address("enp2s0")

    if ip_address.startswith("192.168"):  # Contec
        server = Server(("192.168.54.125", 9999), Handler)
    elif ip_address.startswith("10.249"):  # Arch dev
        server = Server(("10.249.255.151", 9999), Handler)
    server.add_controller(stick_body)

    try:
        server.serve_forever()
    finally:
        logging.info("Shutting down...")
        joystick.Controller.quit_all()
    logging.info("All done")
