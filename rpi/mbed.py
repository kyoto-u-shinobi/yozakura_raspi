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


#def connect_to_mbeds():
#    mbed_arm = None
#    mbed_body = None
#
#    try:
#        mbed = serial.Serial("/dev/ttyACM0", baudrate=38400)
#    except serial.SerialException:
#        raise NoMbedError
#    try:
#        reply = _identify_mbed(mbed)
#    except YozakuraTimeoutError:
#        mbed_arm = mbed
#        #raise UnknownMbedError
#    else:
#        #if reply == "arm":
#            #mbed_arm = mbed
#        #elif reply == "body":
#        if reply == "body":
#            mbed_body = mbed
#        else:
#            mbed_arm = mbed
#            #raise UnknownMbedError
#
#    try:
#        mbed = serial.Serial("/dev/ttyACM1", baudrate=38400)
#    except serial.SerialException:
#        if mbed_body is not None:
#            logging.warning("Arm mbed is not attached!")
#            return mbed_arm, mbed_body
#        else:
#            raise NoMbedError  # Body mbed not attached.
#    try:
#        reply = _identify_mbed(mbed)
#    except YozakuraTimeoutError:
#        if mbed_arm is not None:
#            raise UnknownMbedError("Multiple arm mbeds are attached")
#        mbed_arm = mbed
#        #raise UnknownMbedError
#    else:
#        #if reply == "arm":
#            #if mbed_arm is not None:
#                #raise UnknownMbedError("Multiple arm mbeds are attached")
#            #mbed_arm = mbed
#        #elif reply == "body":
#        if reply == "body":
#            if mbed_body is not None:
#                raise UnknownMbedError("Multiple body mbeds are attached")
#            mbed_body = mbed
#        else:
#            if mbed_arm is not None:
#                raise UnknownMbedError("Multiple arm mbeds are attached")
#            mbed_arm = mbed
#            #raise UnknownMbedError
#
#    return mbed_arm, mbed_body


@interrupted(0.5)
def _identify_mbed(ser):
    id_request = 0b00000111  # If received, mbed prints the name.
    ser.write(bytes([id_request]))
    time.sleep(0.01);
    return ser.readline().decode().split()[0]


class Mbed(serial.Serial):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    @property
    @interrupted(0.5)
    def data(self):
        return self.read(self.inWaiting()).decode().split("\n")[-2].split()
        #return self.readline().decode().split()

    @property
    def identity(self):
        id_request = 0b00000111
        self.write(bytes([id_request]))
        time.sleep(0.5)
        try:
            return self.data[0]
        except IndexError:
            return "none"


def connect_to_mbeds():
    mbed_arm = None
    mbed_body = None

    try:
        try:
            mbed = Mbed("/dev/ttyACM0", baudrate=38400)
        except serial.SerialException:
            raise NoMbedError
        try:
            reply = mbed.identity
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
            mbed = Mbed("/dev/ttyACM1", baudrate=38400)
        except serial.SerialException:
            if mbed_body is not None:
                logging.warning("Arm mbed is not attached!")
                return mbed_arm, mbed_body
            else:
                raise NoMbedError  # Body mbed not attached.
        try:
            reply = mbed.identity
        except YozakuraTimeoutError:
            if mbed_arm is not None:
                raise UnknownMbedError("Multiple arm mbeds are attached")
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
                if mbed_arm is not None:
                    raise UnknownMbedError("Multiple arm mbeds are attached")
                raise UnknownMbedError
    except (NoMbedError, UnknownMbedError):
        try:
            mbed.close()
        except NameError:
            pass
        if mbed_arm is not None:
            mbed_arm.close()
        if mbed_body is not None:
            mbed_body.close()
        raise

    return mbed_arm, mbed_body
