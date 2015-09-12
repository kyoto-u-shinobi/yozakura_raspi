# (C) 2015  Kyoto University Mechatronics Laboratory
# Released under the GNU General Public License, version 3
"""
Common functions used throughout Yozakura.

"""
import fcntl
from functools import wraps
import logging
import signal
import socket
import struct

from common.exceptions import BadArgError, UnknownIPError, YozakuraTimeoutError


def add_logging_level(name, level):
    """
    Add a logging level to the logger.

    The default logging levels are:

    - 10: DEBUG
    - 20: INFO
    - 30: WARNING
    - 40: ERROR
    - 50: CRITICAL

    Parameters
    ----------
    name : str
        The name of the logging level.
    level : int
        The level to be added.

    Examples
    --------
    >>> import logging
    >>> add_logging_level("verbose", 5)
    >>> logging.basicConfig(level=logging.VERBOSE)
    >>> logging.verbose("A very verbose verbiage.")
    VERBOSE:root:A very verbose verbiage.

    """
    setattr(logging, name.upper(), level)
    logging.addLevelName(level, name.upper())
    setattr(logging, name.lower(), lambda msg, *args, **kwargs:
            logging.log(getattr(logging, name.upper()), msg, *args, **kwargs))
    setattr(logging.Logger, name.lower(), lambda inst, msg, *args, **kwargs:
            inst.log(getattr(logging, name.upper()), msg, *args, **kwargs))


def interrupted(duration, exception=YozakuraTimeoutError, error_message=None):
    """
    Decorator for creating per-function timed interrupts.

    The decorator is specified when the function is declared, and cannot be
    changed on the fly. If the function completes successfully within the
    alloted time limit, the result is returned. Otherwise, an interrupt is
    triggered, which raises the specified exception.

    Parameters
    ----------
    duration : float
        The maximum allowable duration of the function, in seconds.
    exception : Exception, optional
        The exception to raise.
    error_message : str, optional
        The error message to be used. The default message uses the name of the
        function that was interrupted.

    Raises
    ------
    exception
        The function took too long and the interrupt occurred.

    Examples
    --------
    >>> import time
    >>> @interrupted(1)  # Interrupt after one second.
    ... def fast_function():
    ...     time.sleep(0.5)
    ...     print("Slept for 0.5 seconds.")
    >>> @interrupted(1)  # Interrupt after one second.
    ... def slow_function():
    ...     time.sleep(5)
    ...     print("Slept for 5 seconds.")
    >>> fast_function()
    Slept for 0.5 seconds.
    >>> slow_function()
    Traceback (most recent call last):
        ...
    YozakuraTimeoutError: slow_function function call timed out!

    """
    def sigalrm_handler(signum, frame):
        """
        Handle SIGALRM.

        This function is called automatically when SIGALRM is received.

        """
        raise exception

    def interrupt_decorator(func):
        @wraps(func)
        def func_wrapper(*args, **kwargs):
            signal.signal(signal.SIGALRM, sigalrm_handler)
            try:
                signal.setitimer(signal.ITIMER_REAL, duration, 0)
                return func(*args, **kwargs)  # Run until completion.
            except exception:  # Only catch the timeout exception.
                if error_message is not None:
                    raise exception(error_message)
                else:
                    raise exception("{name} function call timed out!".format(
                        name=func.__name__))
            finally:
                signal.alarm(0)  # Turn off the timer.
        return func_wrapper
    return interrupt_decorator


def get_ip_address(interfaces):
    """
    Determine the IP address of a set of local interfaces.

    Uses the Linux SIOCGIFADDR ioctl to find the IP address associated with a
    network interface, given the name of that interface, e.g. "eth0". The
    address is returned as a string containing a dotted quad.

    This is useful, for instance, when initializing a server.

    The code is based on an ActiveState Code Recipe. [#]_

    Parameters
    ----------
    interfaces : str or list of str
        The name or names of the interfaces to be checked. The function goes
        through each item in the list in order.

    Returns
    -------
    address : str
        The IP address of the first valid interface tested.
    interface : str
        The name of the valid interface.

    Raises
    ------
    BadArgError
        Bad inputs are given.
    UnknownIPError
        No interfaces give a valid IP address.

    References
    ----------
    .. [#] Paul Cannon, ActiveState Code. "get the IP address associated with
           a network interface (linux only)"
           http://code.activestate.com/recipes/439094-get-the-ip-address-associated-with-a-network-inter/

    Examples
    --------
    Get the IP address of the device's interfaces.

    >>> get_ip_address("wlan0")  # Connected; returns wlan0.
    '192.168.11.2'
    >>> get_ip_address(["eth0", "wlan0"])  # Both connected; returns eth0.
    '192.168.11.5'
    >>> get_ip_address(["eth1", "wlan0"])  # wlan0 connected; returns wlan0.
    '192.168.11.2'
    >>> get_ip_address("wlan1")  # Does not exist
    Traceback (most recent call last):
        ...
    OSError: [Errno 19] No such device
    >>> get_ip_address(["eth1", "wlan1"])  # Do not exist
    Traceback (most recent call last):
        ...
    OSError: [Errno 19] No such devices

    """
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        if type(interfaces) in (list, tuple):
            interface = interfaces[0]
        else:
            interface = interfaces
        packed = struct.pack("256s", str.encode(interface))
    except TypeError:
        raise BadArgError("`interfaces` must be str or list of str.")

    try:
        address = socket.inet_ntoa(fcntl.ioctl(s.fileno(),
                                               0x8915,  # SIOCGIFADDR
                                               packed)[20:24])
        return address, interface
    except OSError:
        # Go through the sequence until the sequence is exhausted.
        if type(interfaces) in (list, tuple) and len(interfaces) > 1:
            return get_ip_address(interfaces[1:])
        else:
            raise UnknownIPError
    finally:
        s.close()
