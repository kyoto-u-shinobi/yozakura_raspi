# (C) 2015  Kyoto University Mechatronics Laboratory
# Released under the GNU General Public License, version 3
"""
Exceptions used in the entire Yozakura project.

Exceptions in Yozakura are only used when there is a fatal error that would be
dangerous, or would cause the robot to be unable to move or carry out its tasks
properly.

"""


class YozakuraException(Exception):
    """
    Root for all Yozakura exceptions, never raised.

    All custom exceptions derive from ``YozakuraException``. That way, when you
    need to filter out only exceptions caused by the robot (as opposed to, say,
    an error caused by your workstation or installation), you can simply use
    something like this:

    >>> try:
    ...     # Some code
    ... except YozakuraException:
    ...     # Do something
    ... except (KeyboardInterrupt, SystemExit):
    ...     # Exit cleanly
    ... except:
    ...     # Other

    """


class InvalidArgError(YozakuraException):
    """
    Raised when there is an invalid argument.

    Similar to ValueError.

    """


class NoControllerMappingError(YozakuraException):
    """
    Raised when the mapping of the controller buttons is unknown.

    Controller button mappings have to be registered in advance in the
    ``Buttons`` class.

    Parameters
    ----------
    make : str, optional
        The make of the controller. If it is provided, the error message will
        specify the controller.

    """
    def __init__(self, make=None):
        message = "{} has an unknown mapping!"
        if not make:
            make = "This controller"
        super().__init__(message.format(make))


class NoDriversError(YozakuraException):
    """
    Raised when a motor has no drivers enabled.

    For a ``Motor`` to be able to use PWM, it needs either the ``Serial``
    connection to a microcontroller for hardware PWM (preferable if available),
    or a list of Raspberry Pi GPIO pins in order to use soft PWM.

    Parameters
    ----------
    motor : Motor, optional
        The motor which has no drivers. If it is provided, the error message
        will specify the motor.

    """
    def __init__(self, motor=None):
        message = "{} does not have any drivers enabled!"
        if not motor:
            motor = "This motor"
        super().__init__(message.format(motor))


class TooManyMotorsError(YozakuraException):
    """
    Raised when more than four motors are registered.

    The ``MotorPacket`` structure only allows for a motor ID between 0 and 3;
    further motors would not be addressable.
    """
    msg = "Four motors have already been registered!"


class NoMotorsError(YozakuraException):
    """
    Raised when RPi client is run with no motors registered.

    The Raspberry Pi client keeps a list of all motors it needs to control. If
    the client is run with no motors registered, the robot would not be able
    to move.

    """
    msg = "No motors are registered!"


class NoSerialsError(YozakuraException):
    """
    Raised when RPi client is run with no serial devices registered.

    The Raspberry Pi needs to use the microcontroller to obtain position data
    from the two flippers of the robot. That information is used to hold the
    angle when there is no input from the server.

    """
    msg = "No serial devices are registered!"


class I2CSlotBusyError(YozakuraException):
    """
    Raised when an I2C slot is busy.

    This can happen when a device is registered at a given slot, and a new
    (or the same) device is attempted to be added with the same address.

    """
    msg = "A device is already registered at this address!"


class NotCalibratedError(YozakuraException):
    """
    Raised when a sensor is not calibrated.

    Parameters
    ----------
    sensor : Device, optional
        The uncalibrated device. If it is provided, the error message will
        specify the device.

    """
    def __init__(self, device=None):
        message = "{} has not been calibrated yet!"
        if not device:
            device = "This device"
        super().__init__(message.format(device))
