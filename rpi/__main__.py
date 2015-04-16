# (C) 2015  Kyoto University Mechatronics Laboratory
# Released under the GNU General Public License, version 3
import logging

import serial

from common.exceptions import NoMbedError
from common.functions import get_ip_address
from rpi.client import Client
# from rpi.devices import CurrentSensor, IMU
from rpi.motor import Motor


def main():
    client_address = get_ip_address(["eth0", "enp2s0", "wlan0"])

    # Connect to correct server based on local IP address.
    if client_address.startswith("192.168"):  # Contec
        opstn_address = "192.168.54.200"
    elif client_address.startswith("10.249"):  # Lab dev
        opstn_address = "10.249.255.172"

    client = Client(client_address, (opstn_address, 9999))

    logging.debug("Initializing motors")
    motors = [Motor("left_wheel_motor", 11, 12, 13),
              Motor("right_wheel_motor", 15, 16, 18),
              Motor("left_flipper_motor", 31, 32, 33),
              Motor("right_flipper_motor", 35, 36, 37)]

    # logging.debug("Initializing current sensors")
    # current_sensors = [CurrentSensor(0x48, name="left_flipper_current")]

    # logging.debug("Initializing IMUs")
    # imus = [IMU(name="front_imu", address=0x68),
    #         IMU(name="rear_imu", address=0x69)]

    try:
        logging.debug("Connecting to mbed")
        mbed = serial.Serial("/dev/ttyACM0", baudrate=38400)
    except serial.SerialException:
        raise NoMbedError

    logging.debug("Registering peripherals to client")
    client.add_serial_device("mbed", mbed)
    for motor in motors:
        client.add_motor(motor, ser=mbed)
    # for sensor in current_sensors:
    #     client.add_current_sensor(sensor)
    # for imu in imus:
    #     client.add_imu(imu)

    try:
        client.run()
    except KeyboardInterrupt:
        pass
    except SystemExit as e:
        logging.error("Received SystemExit: {e}".format(e=e))
    finally:
        logging.info("Shutting down...")
        Motor.shutdown_all()
        logging.debug("Shutting down connection with mbed")
        mbed.close()
        client.shutdown()

    logging.info("All done")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
