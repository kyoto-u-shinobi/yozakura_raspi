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


@interrupted(0.5)
def _identify_mbed(ser):
    id_request = 0b00000111  # If received, mbed prints the name.
    ser.write(bytes([id_request]))
    time.sleep(0.01);
    return ser.readline().decode().split()[0]


class Mbed(serial.Serial):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._logger = logging.getLogger("mbed")

    @property
    @interrupted(0.5)
    def data(self):
        #try:
            #return self.read(self.inWaiting()).decode().split("\n")[-2].split()
        #except IndexError:
            #return ""
        try:
            return self.readline().decode().split()
        except (OSError, TypeError):
            self._logger.warning("An error occured!")
            return [""]

    @property
    def identity(self):
        id_request = 0b00000111
        self.write(bytes([id_request]))
        time.sleep(0.1)
        try:
            return self.data[0]
        except IndexError:
            return "none"

    def write(self, *args, **kwargs):
        try:
            super().write(*args, **kwargs)
        except OSError:
            self._logger.warning("OSError occured!")
            pass


def connect_to_mbeds():
    mbed_arm = None
    mbed_body = None

    try:
        try:
            mbed = Mbed("/dev/ttyACM0", baudrate=38400)
        except serial.SerialException:
            raise NoMbedError("No mbeds are connected")
        try:
            mbed.read(mbed.inWaiting())
            reply = mbed.identity
        except YozakuraTimeoutError:
            raise UnknownMbedError("First mbed is not responding")
        else:
            if reply == "arm":
                mbed_arm = mbed
            elif reply == "body":
                mbed_body = mbed
            else:
                raise UnknownMbedError("Bad reply")

        try:
            mbed = Mbed("/dev/ttyACM1", baudrate=38400)
        except serial.SerialException:
            if mbed_body is not None:
                logging.warning("Arm mbed is not attached!")
                return mbed_arm, mbed_body
            else:
                raise NoMbedError  # Body mbed not attached.
        try:
            mbed.read(mbed.inWaiting())
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

    mbed_arm._logger.name = "mbed-arm"
    mbed_body._logger.name = "mbed-body"

    return mbed_arm, mbed_body
