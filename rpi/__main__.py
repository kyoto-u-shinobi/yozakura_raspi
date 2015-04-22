# (C) 2015  Kyoto University Mechatronics Laboratory
# Released under the GNU General Public License, version 3
import logging

from common.functions import get_ip_address
from rpi.client import Client
# from rpi.devices import CurrentSensor, IMU
from rpi.mbed import connect_to_mbeds
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
    motors = [Motor("left_wheel_motor", 8, 10, 7, max_speed=0.6),
              Motor("right_wheel_motor", 11, 13, 7, max_speed=0.6),
              Motor("left_flipper_motor", 22, 24, 7, max_speed=0.3),
              Motor("right_flipper_motor", 19, 21, 7, max_speed=0.3)]

    # logging.debug("Initializing current sensors")
    # current_sensors = [CurrentSensor(0x48, name="left_flipper_current")]

    # logging.debug("Initializing IMUs")
    # imus = [IMU(name="front_imu", address=0x68),
    #         IMU(name="rear_imu", address=0x69)]

    logging.debug("Connecting to mbeds")
    mbed_arm, mbed_body = connect_to_mbeds()

    logging.debug("Registering peripherals to client")
    if mbed_arm is not None:
        client.add_serial_device("mbed_arm", mbed_arm)
    client.add_serial_device("mbed_body", mbed_body)
    for motor in motors:
        client.add_motor(motor, ser=mbed_body)
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
        mbed_arm.close()
        mbed_body.close()
        client.shutdown()

    logging.info("All done")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
