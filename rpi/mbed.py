# (C) 2015  Kyoto University Mechatronics Laboratory
# Released under the GNU General Public License, version 3
"""
Functions for use with the mbeds.

"""
import logging
import serial

from common.exceptions import NoMbedError, UnknownMbedError,\
    YozakuraTimeoutError
from common.functions import interrupted
from rpi.bitfields import MotorPacket


def connect_to_mbeds():
    try:
        mbed = serial.Serial("/dev/ttyACM0", baudrate=38400)
    except serial.SerialException:
        raise NoMbedError

    try:
        reply = _identify_mbed(mbed)
    except YozakuraTimeoutError:
        mbed_arm = mbed
        arm_at_zero = True
    else:
        if reply == "body":
            mbed_body = mbed
            arm_at_zero = False
        else:
            raise UnknownMbedError

    if arm_at_zero:
        try:
            mbed_body = serial.Serial("/dev/ttyACM1", baudrate=38400)
        except serial.SerialException:
            raise NoMbedError  # Body mbed not attached.
    else:
        try:
            mbed_arm = serial.Serial("/dev/ttyACM1", baudrate=38400)
        except serial.SerialException:
            logging.warning("Arm mbed is not attached!")
            mbed_arm = None

    return mbed_arm, mbed_body


@interrupted(0.5)
def _identify_mbed(ser):
    # Set up special request.
    id_request = MotorPacket()
    id_request.motor_id = 3
    id_request.negative = True
    id_request.speed = 0

    ser.write(bytes([id_request.as_byte]))
    return ser.readline().decode()
