# (C) 2015  Kyoto University Mechatronics Laboratory
# Released under the GNU General Public License, version 3
"""
Common functions used throughout Yozakura.

"""
from collections import namedtuple
from functools import wraps
import logging
import re
import signal
import subprocess

from common.exceptions import UnknownIPError, YozakuraTimeoutError


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


def get_interfaces(external=False, active=False):
    """
    Get a list of network interfaces on Linux.

    To access the MAC address and/or the IP address, set the relevant keyword
    arguments to True.

    Parameters
    ----------
    external : bool, optional
        Only show external interfaces, and ignore virtual (e.g. loopback)
        devices, and return their MAC addresses.
    active : bool, optional
        Only show interfaces which are UP and have an IP address, and return
        their IPv4 addresses.

    Returns
    -------
    interfaces
        list of str containing the interface name by default, or list of
        namedtuple containing `name`, `mac`, and `ip` as requested.

    Raises
    ------
    UnknownIPError
        No external interfaces have a valid IP address.

    Examples
    --------
    >>> print(get_interfaces())
    ['eth0', 'lo', 'wlan0']
    >>> print(get_interfaces(external=True))
    [Interface(name='eth0', mac='a0:b1:c2:d3:e4:f5'), Interface(name='wlan0', ma
    c='f5:e4:d3:c2:b1:a0')]
    >>> print(get_interfaces(ip=True))
    [Interface(name='lo', ip='127.0.0.1'), Interface(name='wlan0', ip='192.168.1
    1.2')]
    >>> print(get_interfaces(external=True, ip=True))
    [Interface(name='wlan0', mac='f5:e4:d3:c2:b1:a0', ip='192.168.11.2')]

    """
    name_pattern = "^(\w+)\s"
    mac_pattern = ".*?HWaddr[ ]([0-9A-Fa-f:]{17})" if external else ""
    ip_pattern = ".*?\n\s+inet[ ]addr:((?:\d+\.){3}\d+)" if active else ""
    pattern = re.compile("".join((name_pattern, mac_pattern, ip_pattern)),
                         flags=re.MULTILINE)

    ifconfig = subprocess.check_output("ifconfig").decode()
    interfaces = pattern.findall(ifconfig)
    if external or active:
        if external and active and not interfaces:
            raise UnknownIPError
        Interface = namedtuple("Interface", "name {mac} {ip}".format(
            mac="mac" if external else "",
            ip="ip" if active else ""))
        return [Interface(*interface) for interface in interfaces]
    else:
        return interfaces
