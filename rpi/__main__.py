# (C) 2015  Kyoto University Mechatronics Laboratory
# Released under the GNU General Public License, version 3
import logging
import serial

from common.networking import get_ip_address
from rpi.client import Client
from rpi.motor import Motor

def main():
    logging.debug("Connecting to server")
    try:
        ip_address = get_ip_address("eth0")
    except OSError:
        ip_address = get_ip_address("enp2s0")

    # Connect to correct server based on local IP address.
    if ip_address.startswith("192.168"):  # Contec
        client = Client(("192.168.54.125", 9999))
    elif ip_address.startswith("10.249"):  # Arch dev
        client = Client(("10.249.255.151", 9999))

    logging.debug("Initializing motors")
    left_motor = Motor("left_motor", 11, max_speed=0.6)
    right_motor = Motor("right_motor", 38, max_speed=0.6)

    try:
        logging.debug("Connecting mbed")
        mbed_ser = serial.Serial("/dev/ttyACM0", 9600)
        logging.debug("Registering motors to client")
        client.add_motor(left_motor, ser=mbed_ser)
        client.add_motor(right_motor, ser=mbed_ser)
    except serial.SerialException:
        logging.warning("The mbed is not connected!")

    try:
        client.run()
    finally:
        logging.info("Shutting down...")
        Motor.shutdown_all()
        try:
            logging.debug("Shutting down connection with mbed")
            mbed_ser.close()
        except NameError:
            logging.debug("The mbed was not connected")
            pass
        client.shutdown()
    logging.info("All done")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
