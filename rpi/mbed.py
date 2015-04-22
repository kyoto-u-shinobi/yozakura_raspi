# (C) 2015  Kyoto University Mechatronics Laboratory
# Released under the GNU General Public License, version 3
"""
Functions for use with the mbeds.

"""
import logging
import serial
import time

from common.exceptions import NoMbedError, UnknownMbedError,\
    YozakuraTimeoutError
from common.functions import interrupted
from rpi.bitfields import MotorPacket


def connect_to_mbeds():
    mbed_arm = None
    mbed_body = None
    
    try:
        mbed = serial.Serial("/dev/ttyACM0", baudrate=38400)
    except serial.SerialException:
        raise NoMbedError
    try:
        reply = _identify_mbed(mbed)
    except YozakuraTimeoutError:
        raise UnknownMbedError
    else:
        if reply == "arm":
            mbed_arm = mbed
        elif reply == "body":
            mbed_body = mbed
        else:
            raise UnknownMbedError

    try:
        mbed = serial.Serial("/dev/ttyACM1", baudarate=38400)
    except serial.SerialException:
        if mbed_body is not None:
            logging.warning("Arm mbed is not attached!")
        else:
            raise NoMbedError  # Body mbed not attached.
    try:
        reply = _identify_mbed(mbed)
    except YozakuraTimeoutError:
        raise UnknownMbedError
    else:
        if reply == "arm":
            if mbed_arm is not None:
                raise UnknownMbedError("Multiple arm mbeds are attached")
            mbed_arm = mbed
        elif reply == "body":
            if mbed_body is not None:
                raise UnknownMbedError("Multiple body mbeds are attached")
            mbed_body = mbed
        else:
            raise UnknownMbedError
            
    return mbed_arm, mbed_body


@interrupted(0.5)
def _identify_mbed(ser):
    # Set up special request.
    id_request = MotorPacket()
    id_request.motor_id = 3
    id_request.negative = True
    id_request.speed = 0

    ser.write(bytes([id_request.as_byte]))
    time.sleep(0.01);
    return ser.read(ser.inWaiting()).decode().split("\n")[-2]
