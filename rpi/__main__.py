# (C) 2015  Kyoto University Mechatronics Laboratory
# Released under the GNU General Public License, version 3
import logging
import serial

from common.networking import get_ip_address
from rpi.client import Client
from rpi.motor import Motor
from rpi.server import Server, Handler


def main():
    logging.debug("Connecting to server")
    try:
        ip_address = get_ip_address("eth0")
    except OSError:
        ip_address = get_ip_address("enp2s0")

    # Connect to correct server based on local IP address.
    if ip_address.startswith("192.168"):  # Contec
        opstn_address = "192.168.54.125"
    elif ip_address.startswith("10.249"):  # Arch dev
        opstn_address = "10.249.255.151"

    client = Client((opstn_address, 9999))

    logging.debug("Initializing motors")
    left_motor = Motor("left_motor", 11, 12, 13)
    right_motor = Motor("right_motor", 15, 16, 18)
    left_flipper = Motor("left_flipper", 31, 32, 33)
    right_flipper = Motor("right_flipper", 35, 36, 37)

    try:
        logging.debug("Connecting mbed")
        mbed = serial.Serial("/dev/ttyACM0", 9600)
        client.add_serial_device("mbed", mbed)
        
        logging.debug("Registering motors to client")
        client.add_motor(left_motor, ser=mbed)
        client.add_motor(right_motor, ser=mbed)
        client.add_motor(left_flipper, ser=mbed)
        client.add_motor(right_flipper, ser=mbed)
    except serial.SerialException:
        logging.warning("The mbed is not connected")
    
    try:
        client.run()
    finally:
        logging.info("Shutting down...")
        server_process.terminate()
        Motor.shutdown_all()
        try:
            logging.debug("Shutting down connection with mbed")
            mbed.close()
        except NameError:
            logging.debug("The mbed was not connected")
            pass
        client.shutdown()
        
    logging.info("All done")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
