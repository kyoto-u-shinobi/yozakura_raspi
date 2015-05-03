# (C) 2015  Kyoto University Mechatronics Laboratory
# Released under the GNU General Public License, version 3
import logging

import serial

from common.exceptions import NoConnectionError, NoMbedError, UnknownMbedError, YozakuraTimeoutError, I2CSlotEmptyError, DynamixelError
from common.functions import get_ip_address
from rpi.arm import Arm
from rpi.client import Client
from rpi.dynamixel import AX12, MX28
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

    logging.info("Initializing motors")
    motors = [Motor("left_wheel_motor", 8, 10, 7, max_speed=0.4),
              Motor("right_wheel_motor", 11, 13, 7, max_speed=0.4),
              Motor("left_flipper_motor", 22, 24, 7, max_speed=0.4),
              Motor("right_flipper_motor", 19, 21, 7, max_speed=0.4)]

    logging.info("Initializing current sensors")
    current_sensors = []
    for address, name in zip(range(0x40, 0x44), ["left_wheel_current",
                                                 "right_wheel_current",
                                                 "left_flipper_current",
                                                 "right_flipper_current"]):
        try:
            sensor = CurrentSensor(address=address, name=name)
        except I2CSlotEmptyError as e:
            logging.warning(e)
        else:
            current_sensors.append(sensor)

    logging.info("Initializing IMUs")
    imus=[]
    for address, name in zip([0x68, 0x69], ["rear_imu", "front_imu"]):
        try:
            imu=IMU(address=address, name=name)
        except I2CSlotEmptyError as e:
            logging.warning(e)
        else:
            imus.append(imu)

    logging.info("Connecting to mbeds")
    try:
        mbed_arm, mbed_body = connect_to_mbeds()
    except (NoMbedError, UnknownMbedError, YozakuraTimeoutError) as e:
        logging.critical(e)
        Motor.shutdown_all()
        client.shutdown()
        return

    logging.info("Initializing arm")
    arm = Arm()
    linear = pitch = yaw = None
    try:
        linear = AX12(0, name="linear")
        pitch = MX28(1, name="pitch")
        yaw = MX28(2, name="yaw")
        servos = (linear, pitch, yaw)

        arm.add_servo(linear, home_position=300, limits=(100, 300), speed=30, upstep=20, downstep=20, multiturn=False)
        arm.add_servo(pitch, home_position=334, limits=(172, 334), speed=30, upstep=20, downstep=20, multiturn=False)
        arm.add_servo(yaw, home_position=0, limits=(360, 360), speed=30, upstep=20, downstep=20, multiturn=True)
    except DynamixelError as e:
        logging.critical(e)
        for servo in [linear, pitch, yaw]:
            try:
                servo.close()
            except AttributeError:
                pass
        return
    
    for servo in servos:
        arm.add_servo(servo)
    
    arm.go_home_loop()

    logging.debug("Registering peripherals to client")
    if mbed_arm is not None:
        client.add_serial_device("mbed_arm", mbed_arm)
    client.add_serial_device("mbed_body", mbed_body)
    client.add_arm(arm)
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
        print()
    except SystemExit as e:
        logging.error("Received SystemExit: {e}".format(e=e))
    finally:
        logging.info("Shutting down...")
        Motor.shutdown_all()
        logging.debug("Shutting down connection with mbed")
        if mbed_arm is not None:
            mbed_arm.close()
        mbed_body.close()
        logging.debug("Shutting down arm")
        for servo in servos:
            servo.close()
        client.shutdown()

    logging.info("All done")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(name)-30s : %(levelname)-8s %(message)s")
    main()
