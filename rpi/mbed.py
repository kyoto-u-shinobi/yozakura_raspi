# (C) 2015  Kyoto University Mechatronics Laboratory
# Released under the GNU General Public License, version 3
"""
Functions for use with the mbeds.

"""
import glob
import logging
import shutil
import time

import serial

from common.exceptions import NoMbedError, UnknownMbedError,\
    YozakuraTimeoutError
from common.functions import interrupted


class Mbed(serial.Serial):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._logger = logging.getLogger("mbed")

    @property
    @interrupted(0.2)
    def data(self):
        try:
            data = self.read(self.inWaiting()).decode().split("\n")
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

def _fix_port_numbers():
    ports = glob.glob("/dev/ttyACM*")
    port_numbers = [int(i.split("/dev/ttyACM")[1]) for i in ports]
    extra_numbers = [n for n in port_numbers if n > 1]
    for i in range(2):
        if i not in port_numbers:
            if extra_numbers:
                shutil.move("/dev/ttyACM{}".format(extra_numbers.pop()),
                            "/dev/ttyACM{}".format(i))
    if extra_numbers:
        logger.warning("ACM ports still active: {}".format(extra_numbers))

def connect_to_mbeds():
    _fix_port_numbers()

    mbed = mbed_arm = mbed_body = None

    try:
        try:
            mbed = Mbed("/dev/ttyACM0", baudrate=38400)
        except serial.SerialException:
            raise NoMbedError("No mbeds are connected")
        reply = mbed.identity
        if reply == "arm":
            mbed_arm = mbed
        elif reply == "body":
            mbed_body = mbed
        elif reply == "none":
            logging.warning("The first mbed did not reply")
        else:
            raise UnknownMbedError("The first mbed sent a bad reply")

        try:
            mbed = Mbed("/dev/ttyACM1", baudrate=38400)
        except serial.SerialException:
            if mbed_body is not None:
                logging.warning("Arm mbed is not attached")
                return mbed_arm, mbed_body
            else:
                raise NoMbedError("Body mbed is not attached!")
        reply = mbed.identity
        if reply == "arm":
            if mbed_arm is not None:
                raise UnknownMbedError("Multiple arm mbeds are attached")
            mbed_arm = mbed
        elif reply == "body":
            if mbed_body is not None:
                raise UnknownMbedError("Multiple body mbeds are attached")
            mbed_body = mbed
        elif reply == "none":
            if mbed_body is not None:
                logging.warning("The second mbed did not reply. Is the arm on?")
            else:
                raise NoMbedError("Body mbed is not attached!")
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
        mbed_arm._logger.debug("mbed initialized")
    mbed_body._logger.name = "mbed-body"
    mbed_body._logger.debug("mbed initialized")

    return mbed_arm, mbed_body
