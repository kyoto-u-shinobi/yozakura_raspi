# (C) 2015  Kyoto University Mechatronics Laboratory
# Released under the GNU General Public License, version 3
from common.networking import get_ip_address
from rpi.client import Client
import logging
import serial

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    try:
        ip_address = get_ip_address("eth0")
    except OSError:
        ip_address = get_ip_address("enp2s0")

    if ip_address.startswith("192.168"):  # Contec
        client = Client(("192.168.54.125", 9999))
    elif ip_address.startswith("10.249"):  # Arch dev
        client = Client(("10.249.255.151", 9999))
    
    try:
        mbed_ser = serial.Serial("/dev/ttyACM0", 9600)
    except serial.SerialException:
        logging.warning("mbed is not connected!")
