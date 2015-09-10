# (C) 2015  Kyoto University Mechatronics Laboratory
# Released under the GNU General Public License, version 3
import logging

from common.exceptions import YozakuraTimeoutError, NoConnectionError,\
    NoMbedError, UnknownMbedError, I2CSlotEmptyError
from common.functions import add_logging_level, get_ip_address
from rpi.client import Client
from rpi.devices import CurrentSensor, IMU
from rpi.mbed import Mbed
from rpi.motor import Motor


def main():
    client_address = get_ip_address(["eth0", "enp2s0", "wlan0"])[0]

    # Connect to correct server based on local IP address.
    if client_address.startswith("192.168"):  # Contec
        opstn_address = "192.168.54.200"
    elif client_address.startswith("10.249"):  # Lab dev
        opstn_address = "10.249.255.172"

    try:
        client = Client(client_address, (opstn_address, 9999))
    except NoConnectionError as e:
        logging.critical(e.split("! ")[0])
        logging.help(e.split("! ")[1])
        return

    logging.info("Initializing motors")
    motors = [Motor("left_wheel_motor", 8, 10, 7, max_speed=0.8),
              Motor("right_wheel_motor", 11, 13, 7, max_speed=0.8),
              Motor("left_flipper_motor", 22, 24, 7, max_speed=0.4),
              Motor("right_flipper_motor", 19, 21, 7, max_speed=0.4)]

    logging.info("Initializing current sensors")
    current_sensors = []
    # TODO (masasin): Add alert pins.
    for address, name in zip([0x40, 0x41, 0x42, 0x42],
                             ["left_wheel_current", "right_wheel_current",
                              "left_flipper_current", "right_flipper_current"]):
        try:
            sensor = CurrentSensor(address=address, name=name)
        except I2CSlotEmptyError as e:
            logging.warning(e)
        else:
            current_sensors.append(sensor)

    logging.info("Initializing IMUs")
    imus = []
    for address, name in zip([0x68, 0x69], ["rear_imu", "front_imu"]):
        try:
            imu = IMU(address=address, name=name)
        except I2CSlotEmptyError as e:
            logging.warning(e)
        else:
            imus.append(imu)

    logging.info("Connecting to mbeds")
    try:
        mbed_arm, mbed_body = Mbed.connect_to_mbeds()
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
    except NoConnectionError:
        pass
    except KeyboardInterrupt:
        print()  # Keep the console log aligned
    finally:
        logging.info("Shutting down...")
        Motor.shutdown_all()
        logging.debug("Shutting down connections with mbeds")
        if mbed_arm is not None:
            mbed_arm.close()
        mbed_body.close()
        client.shutdown()

    logging.info("All done")

if __name__ == "__main__":
    format_string = "%(name)-30s : %(levelname)-8s  %(message)s"
    date_format = "%Y-%m-%d %H:%M:%S "
    add_logging_level("verbose", 5)
    add_logging_level("help", 25)

    LOG_TO_FILE = False

    if LOG_TO_FILE:
        # Log everything to file
        logging.basicConfig(level=logging.DEBUG,
                            format="%(asctime)s " + format_string,
                            datefmt=date_format,
                            filename="/tmp/rpi.log",
                            filemode="w")

        # Log important data to console
        console = logging.StreamHandler()
        console.setLevel(logging.INFO)
        console.setFormatter(logging.Formatter(format_string))
        logging.getLogger("").addHandler(console)
    else:
        logging.basicConfig(level=logging.INFO, format=format_string)

    # Run Yozakura
    main()
