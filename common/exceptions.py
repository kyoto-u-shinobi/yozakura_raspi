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


class BadArgError(YozakuraException):
    """
    Raised when there is an invalid argument.

    Similar to ValueError.

    """


class BadDataError(YozakuraException):
    """
    Raised when there is invalid data.

    Similar to ValueError.

    """


class UnknownMbedError(YozakuraException):
    """Raised when the raspberry pi connects to an unknown mbed."""
    msg = "An mbed cannot be identified!"


class NoMbedError(YozakuraException):
    """Raised when the raspberry pi cannot connect to an mbed."""
    msg = "An mbed is not connected!"


class NoControllerError(YozakuraException):
    """Raised when there are no controllers connected to the base station."""
    msg = "There are no controllers attached!"


class UnknownControllerError(YozakuraException):
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
        message = "{make} has an unknown mapping!"
        if not make:
            make = "This controller"
        super().__init__(message.format(make=make))


class NoDriversError(YozakuraException):
    """
    Raised when a motor driver has no control method enabled.

    For a ``Motor`` to be able to use PWM, it needs either the ``Serial``
    connection to a microcontroller for hardware PWM (preferable if available),
    or a list of Raspberry Pi GPIO pins in order to use software PWM.

    Parameters
    ----------
    motor : Motor, optional
        The motor which has no control methods. If it is provided, the error
        message will specify the motor.

    """
    def __init__(self, motor=None):
        message = "{motor} does not have any drivers enabled!"
        if not motor:
            motor = "This motor"
        super().__init__(message.format(motor=motor))


class MotorCountError(YozakuraException):
    """
    Raised when not enough motors, or more than four motors are registered.

    The Raspberry Pi client keeps a list of all motors it needs to control. If
    the client is run with no motors registered, the robot would not be able
    to move.

    In addition, the ``MotorPacket`` structure only allows for a motor ID
    between 0 and 3; further motors would not be addressable.

    Parameters
    ----------
    count : int, optional
        The amount of motors that have been registered.

    """
    def __init__(self, count=None):
        if count is None:
            message = "The motor count is bad!"
        elif count == 1:
            message = "Only one motor has been added!"
        elif count < 4:
            message = "Only {n} motors have been added!".format(n=count)
        else:
            message = "{n} motors have already been added!".format(n=count)
        super().__init__(message)


class NoSerialsError(YozakuraException):
    """
    Raised when RPi client is run with both serial devices not registered.

    The Raspberry Pi needs to use the microcontroller to obtain position data
    from the two flippers of the robot, as well as sensor data from the arm.

    """
    msg = "Insufficient serial devices are registered!"


class I2CSlotEmptyError(YozakuraException):
    """
    Raised when no device is found at a given address.

    Parameters
    ----------
    address : int, optional
        The address at which the error occured. If it is provided, the error
        message will specify the address.

    """
    def __init__(self, address=None):
        message = "The I2C slot at {addr} contains no devices!"
        if not address:
            address = "this address"
        else:
            address = hex(address)
        super().__init__(message.format(addr=address))


class I2CSlotBusyError(YozakuraException):
    """
    Raised when an I2C slot is busy.

    This can happen when a device is registered at a given slot, and a new
    (or the same) device is attempted to be added with the same address.

    Parameters
    ----------
    address : int, optional
        The address at which the error occured. If it is provided, the error
        message will specify the address.

    """
    def __init__(self, address=None):
        message = "The I2C slot at {addr} is busy!"
        if not address:
            address = "this address"
        else:
            address = hex(address)
        super().__init__(message.format(addr=address))


class NotCalibratedError(YozakuraException):
    """
    Raised when a device has not been calibrated.

    Parameters
    ----------
    device : Device, optional
        The uncalibrated device. If it is provided, the error message will
        specify the device.

    """
    def __init__(self, device=None):
        message = "{dev} has not been calibrated yet!"
        if not device:
            device = "This device"
        super().__init__(message.format(dev=device))


class YozakuraTimeoutError(YozakuraException):
    """
    Raised when a Timeout occurs.

    Similar to TimeoutError.

    """