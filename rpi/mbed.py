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
    id_request = 0b00000111  # If received, mbed prints the name.
    ser.write(bytes([id_request]))
    time.sleep(0.01);
    return ser.readline().decode().split("\n")
