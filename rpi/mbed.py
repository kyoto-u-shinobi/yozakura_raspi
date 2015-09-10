# (C) 2015  Kyoto University Mechatronics Laboratory
# Released under the GNU General Public License, version 3
"""
Provides the Mbed class to interface with the mbed.

The mbeds used in Yozakura are both LPC1768. [#]_


References
----------
.. [#] ARM mbed, mbed LPC1768.
       https://developer.mbed.org/platforms/mbed-LPC1768/
"""
import glob
import logging
import shutil
import time

import serial

from common.exceptions import NoMbedError, UnknownMbedError
from common.functions import interrupted


class Mbed(serial.Serial):
    """
    mbed LPC1768. [#]_

    This class subclasses from `serial.Serial`, and implements all its
    methods, and also provides some new ones. For in-depth implementation
    details, please see the `pyserial` documentation.

    Parameters
    ----------
    port : str
        Device name or port number.
    baurdate : int, optional
        The baudrate with which to communicate with the mbed.

    See Also
    --------
    serial.Serial

    References
    ----------
    .. [#] ARM mbed, mbed LPC1768.
           https://developer.mbed.org/platforms/mbed-LPC1768/

    """
    def __init__(self, *args, **kwargs):
        self._identity = None
        self._logger = logging.getLogger("mbed-{port}".format(port=port))
        self._logger.debug("Initializing mbed")
        try:
            super().__init__(*args, **kwargs)
        except serial.SerialException:
            self._logger.warning("mbed not connected")
        else:
            self._logger = logging.getLogger("mbed-{mbed_id}"
                                             .format(mbed_id=self.identity))
            self._logger.debug("mbed initialized")

    @property
    @interrupted(0.2)
    def data(self):
        """
        Return the latest line in the mbed's output buffer.

        If the buffer contains output with no endline, wait for the rest of the
        line to be printed.

        This method will be interrupted after 0.2 seconds if it has not finished
        by then.

        Returns
        -------
        list of str
            The latest line of data, split at spaces. If the data is invalid,
            returns a list containing a single empty string.

        """
        self._logger.debug("Reading data")
        try:
            data = self.read(self.inWaiting()).decode().split("\n")
            if not data[-1]:
                return data[-2].split()
            else:
                return (data[-1] + self.readline().decode()).split()
        except IndexError:
            return [""]
        except (OSError, TypeError) as e:
            self._logger.warning("An unknown error occured: {}".format(e))
            return [""]

    @property
    def identity(self):
        """
        Return the ID as reported by the mbed.

        The mbed must return a string containing its ID when it receives a char
        with a value of 0x7. In addition, asynchronous mbeds must not produce
        any new output until the identity has been read (i.e., after a delay
        of one second).

        In order to speed up subsequent reads, the value of identity is cached.

        Returns
        -------
        str
            The identity of the mbed, or None if no data was returned.
        """
        if not self._identity:
            self.write(bytes([7]))
            time.sleep(1)
            data = self.data[0]
            if not data:
                return None
            else:
                self._identity = data

        return self._identity

    def write(self, data):
        """
        Write the string data to the port.

        Parameters
        ----------
        data : str
            The data to be sent.

        Returns
        -------
        int
            The number of bytes written.

        """
        self._logger.debug("Writing data")
        try:
            super().write(data)
        except OSError as e:
            self._logger.warning("OSError occured: {e}".format(e=e))
        else:
            self._logger.debug("Wrote data")

    def close(self):
        """Close the port immediately."""
        self._logger.debug("Closing mbed")
        super().close()
        self._logger.debug("mbed closed")

    @staticmethod
    def connect_to_mbeds():
        """
        Connect to the arm and body mbed, if attached.

        This method requires the body mbed to be attached, and the arm mbed is
        optional.

        Returns
        -------
        mbed_arm : Mbed
            The mbed connected to Yozakura's arm, and the sensors on the arm.
        mbed_body : Mbed
            The mbed connected to the motors and the potentiometer giving the
            flipper positions.

        Raises
        ------
        NoMbedError
            The body mbed is not attached, or no mbeds are attached at all.
        UnknownMbedError:
            Multiple mbeds with the same identity are attached, or an mbed with
            an unknown identity is attached.

        """
        mbed = mbed_arm = mbed_body = None
        no_reply = False

        try:
            for port in glob.glob("/dev/ttyACM*"):
                mbed = Mbed(port, baudrate=38400)
                identity = mbed._identity
                if identity is None:
                    logging.warning("The mbed at {p} did not reply"
                                    .format(p=port))
                    no_reply = True
                elif identity == "arm":
                    if mbed_arm:
                        raise UnknownMbedError("Multiple arm mbeds attached")
                    mbed_arm = mbed
                elif identity == "body":
                    if mbed_body:
                        raise UnknownMbedError("Multiple body mbeds attached")
                    mbed_body = mbed
                else:
                    raise UnknownMbedError("The mbed at {p} has bad ID: {ident}"
                                           .format(p=port, ident=identity))

            if not mbed_body:
                raise NoMbedError("The body mbed is not connected!")
            if not mbed_arm:
                logging.warning("The arm mbed is not connected!")
                if no_reply:
                    logging.help("Is the arm on?")

        except (NoMbedError, UnknownMbedError):
            [device.close() for device in (mbed, mbed_arm, mbed_body) if device]
            raise

        return mbed_arm, mbed_body

    @staticmethod
    def _fix_port_numbers():
        """
        Ensure that port numbers start at /dev/ttyACM0 and increase in order.

        For instance, if mbeds were attached to both /dev/ttyACM0 and
        /dev/ttyACM1, but one mbed was physically disconnected and quickly
        reconnected, it would be attached automatically to /dev/ttyACM2.

        """
        ports = glob.glob("/dev/ttyACM*")
        port_numbers = [int(i.split("/dev/ttyACM")[1]) for i in ports]
        extra_numbers = [n for n in port_numbers if n >= 2]
        if not port_numbers:
            raise NoMbedError("No mbeds are connected")
        elif len(port_numbers) == 1 and port_numbers[0] != 0:
            shutil.move("/dev/ttyACM{}".format(port_numbers[0]), "/dev/ttyACM0")
        for i in range(2):
            if i not in port_numbers:
                if extra_numbers:
                    shutil.move("/dev/ttyACM{}".format(extra_numbers.pop()),
                                "/dev/ttyACM{}".format(i))
        if extra_numbers:
            logging.warning("ACM ports still active: {}".format(extra_numbers))
