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


class Mbed(serial.Serial):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._logger = logging.getLogger("mbed")

    @property
    @interrupted(0.5)
    def data(self):
        try:
            data = self.read(self.inWaiting()).decode().split("\n")
            #print(data)
            if not data[-1]:
                return data[-2].split()
            else:
                return (data[-1] + self.readline().decode()).split()
        except IndexError:
            return [""]
        except (OSError, TypeError) as e:
            self._logger.warning("An error occured: {}".format(e))
            return [""]

    @property
    def identity(self):
        id_request = 0b00000111
        self.write(bytes([id_request]))
        time.sleep(1)
        data = self.data[0]
        if not data:
            return "none"
        else:
            return data

    def write(self, *args, **kwargs):
        try:
            super().write(*args, **kwargs)
        except OSError:
            self._logger.warning("OSError occured!")
            pass


def connect_to_mbeds():
    mbed = mbed_arm = mbed_body = None

    try:
        try:
            mbed = Mbed("/dev/ttyACM0", baudrate=38400)
        except serial.SerialException:
            raise NoMbedError("No mbeds are connected")
        try:
            # mbed.read(mbed.inWaiting())
            reply = mbed.identity
        except YozakuraTimeoutError:
            raise UnknownMbedError("The first mbed is not responding")
        else:
            if reply == "arm":
                mbed_arm = mbed
            elif reply == "body":
                mbed_body = mbed
            else:
                logging.warning("Arm mbed is not attached")
                #raise UnknownMbedError("The first mbed sent a bad reply")

        try:
            mbed = Mbed("/dev/ttyACM1", baudrate=38400)
        except serial.SerialException:
            if mbed_body is not None:
                logging.warning("Arm mbed is not attached")
                return mbed_arm, mbed_body
            else:
                raise NoMbedError("Body mbed is not attached!")
        try:  # Something is attached
            # mbed.read(mbed.inWaiting())
            reply = mbed.identity
        except YozakuraTimeoutError:
            raise UnknownMbedError("The second mbed is not responding")
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
                raise UnknownMbedError("The second mbed sent a bad reply")
    except (NoMbedError, UnknownMbedError):
        if mbed is not None:
            mbed.close()
        if mbed_arm is not None:
            mbed_arm.close()
        if mbed_body is not None:
            mbed_body.close()
        raise

    if mbed_arm is not None:
        mbed_arm._logger.name = "mbed-arm"
    mbed_body._logger.name = "mbed-body"
    # mbed_arm._logger._transfer_size = 195
    # mbed_body._logger._transfer_size = 11

    return mbed_arm, mbed_body
