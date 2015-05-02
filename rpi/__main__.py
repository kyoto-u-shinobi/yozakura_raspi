# (C) 2015  Kyoto University Mechatronics Laboratory
# Released under the GNU General Public License, version 3
import logging

import serial

from common.exceptions import NoConnectionError, NoMbedError, UnknownMbedError, YozakuraTimeoutError
from common.functions import get_ip_address
from rpi.client import Client
from rpi.devices import CurrentSensor, IMU
from rpi.mbed import connect_to_mbeds
from rpi.motor import Motor


def main():
    client_address = get_ip_address(["eth0", "enp2s0", "wlan0"])

    # Connect to correct server based on local IP address.
    if client_address.startswith("192.168"):  # Contec
        opstn_address = "192.168.54.200"
    elif client_address.startswith("10.249"):  # Lab dev
        opstn_address = "10.249.255.172"

    try:
        client = Client(client_address, (opstn_address, 9999))
    except NoConnectionError as e:
        logging.critical(e)
        return

    logging.debug("Initializing motors")
    motors = [Motor("left_wheel_motor", 8, 10, 7, max_speed=0.4),
              Motor("right_wheel_motor", 11, 13, 7, max_speed=0.4),
              Motor("left_flipper_motor", 22, 24, 7, max_speed=0.4),
              Motor("right_flipper_motor", 19, 21, 7, max_speed=0.4)]

    # logging.debug("Initializing current sensors")
    current_sensors = [
                       CurrentSensor(0x40, name="left_motor_current"),
                       CurrentSensor(0x41, name="right_motor_current"),
                       CurrentSensor(0x42, name="left_flipper_current"),
                       CurrentSensor(0x43, name="right_flipper_current")
                       ]

    # logging.debug("Initializing IMUs")
    imus = [
            IMU(name="front_imu", address=0x69),
            IMU(name="rear_imu", address=0x68)
           ]

    logging.debug("Connecting to mbeds")
    try:
        mbed_arm, mbed_body = connect_to_mbeds()
    except (NoMbedError, UnknownMbedError, YozakuraTimeoutError) as e:
        logging.critical(e)
        Motor.shutdown_all()
        client.shutdown()
        return

    logging.debug("Registering peripherals to client")
    if mbed_arm is not None:
        client.add_serial_device("mbed_arm", mbed_arm)
    client.add_serial_device("mbed_body", mbed_body)
    for motor in motors:
        client.add_motor(motor, ser=mbed_body)
    for sensor in current_sensors:
        client.add_current_sensor(sensor)
    for imu in imus:
        client.add_imu(imu)

    try:
        client.run()
    except (KeyboardInterrupt, NoConnectionError):
        pass
    except SystemExit as e:
        logging.error("Received SystemExit: {e}".format(e=e))
    finally:
        logging.info("Shutting down...")
        Motor.shutdown_all()
        logging.debug("Shutting down connection with mbed")
        if mbed_arm is not None:
            mbed_arm.close()
        mbed_body.close()
        client.shutdown()

    logging.info("All done")

if __name__ == "__main__":
    # Create an extra level
    logging.EXTRA = 4
    logging.Logger.extra = lambda inst, msg, *args, **kwargs: inst.log(logging.EXTRA, msg, *args, **kwargs)
    logging.extra = lambda msg, *args, **kwargs: logging.log(logging.EXTRA, msg, *args, **kwargs)

    # Create a verbose level
    logging.VERBOSE = 5
    logging.Logger.verbose = lambda inst, msg, *args, **kwargs: inst.log(logging.VERBOSE, msg, *args, **kwargs)
    logging.verbose = lambda msg, *args, **kwargs: logging.log(logging.VERBOSE, msg, *args, **kwargs)

    format_string = "%(name)-30s : %(levelname)-8s  %(message)s"
    date_format = "%Y-%m-%d %H:%M:%S "
    # Log everything to file
    #logging.basicConfig(level=logging.EXTRA,
            #format="%(asctime)s " + format_string,
            #datefmt="%Y-%m-%d %H:%M:%S",
            #filename="/tmp/rpi.log",
            #filemode="w")

    logging.basicConfig(level=logging.INFO, format=format_string)

    # Log import data to console
    #console = logging.StreamHandler()
    #console.setLevel(logging.INFO)
    #console.setFormatter(logging.Formatter(format_string))
    #logging.getLogger("").addHandler(console)


    # Log everything to file
    #file_logger = logging.FileHandler("/tmp/rpi.log")
    #file_logger.setLevel(logging.INFO)
    #file_logger.setFormatter(logging.Formatter("%(asctime)s " + format_string))
    #file_logger.datefmt = date_format
    #logging.getLogger("").addHandler(file_logger)

    #logging.basicConfig(level=logging.INFO, format="%(name)-30s:%(levelname)-8s  %(message)s")

    main()
