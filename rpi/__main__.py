# (C) 2015  Kyoto University Mechatronics Laboratory
# Released under the GNU General Public License, version 3
import logging
import serial

from common.networking import get_ip_address
from rpi.client import Client
from rpi.devices import CurrentSensor, IMU
from rpi.motor import Motor


def main():
    logging.debug("Connecting to server")
    try:
        ip_address = get_ip_address("eth0")
    except OSError:
        ip_address = get_ip_address("enp2s0")

    # Connect to correct server based on local IP address.
    if ip_address.startswith("192.168"):  # Contec
        opstn_address = "192.168.54.125"
    elif ip_address.startswith("10.249"):  # Lab dev
        opstn_address = "10.249.255.172"

    client = Client((opstn_address, 9999))

    logging.debug("Initializing motors")
    motors = [Motor("left_motor", 11, 12, 13),
              Motor("right_motor", 15, 16, 18),
              Motor("left_flipper", 31, 32, 33),
              Motor("right_flipper", 35, 36, 37)]

    logging.debug("Initializing current sensors")
    current_sensors = [
                       #CurrentSensor(0x48, name="left_flipper_current")
                      ]

    logging.debug("Initializing IMUs")
    imus = [
            IMU(name="front_imu", address=0x68),
            IMU(name="rear_imu", address=0x69)
           ]

    try:
        logging.debug("Connecting mbed")
        mbed = serial.Serial("/dev/ttyACM0", 9600)
        client.add_serial_device("mbed", mbed)
    except serial.SerialException:
        logging.warning("The mbed is not connected")

    logging.debug("Registering motors and sensors to client")
    for motor in motors:
        client.add_motor(motor, ser=mbed)
    for sensor in current_sensors:
        client.add_current_sensor(sensor)
    for imu in imus:
        client.add_imu(imu)

    try:
        client.run()
    finally:
        logging.info("Shutting down...")
        Motor.shutdown_all()
        try:
            logging.debug("Shutting down connection with mbed")
            mbed.close()
        except NameError:
            logging.debug("The mbed was not connected")
        client.shutdown()

    logging.info("All done")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
