# (C) 2015  Kyoto University Mechatronics Laboratory
# Released under the GNU General Public License, version 3
"""
Common functions used throughout Yozakura.

"""
import fcntl
from functools import wraps
import signal
import socket
import struct

from common.exceptions import YozakuraTimeoutError


def interrupted(duration, exception=YozakuraTimeoutError, error_message=None):
    """
    Decorate for creating per-function interrupts.

    Parameters
    ----------
    duration : float
        The maximum allowable duration of the function.
    exception : Exception, optional
        The exception to raise.
    error_message : str, optional
        The error message to be used.

    Examples
    --------
    >>> import time
    >>> @interrupted(1)
    ... def slow_func_1():
    ...     time.sleep(5)
    Traceback (most recent call last):
        ...
    YozakuraTimeoutError: slow_func_1 function call timed out!


    """
    def sigalrm_handler(signum, frame):
        """
        Handle SIGALRM.

        This function is automatically called by the Linux Kernel.

        """
        raise exception

    def interrupt_decorator(func):
        @wraps(func)
        def func_wrapper(*args, **kwargs):
            signal.signal(signal.SIGALRM, sigalrm_handler)
            try:
                signal.setitimer(signal.ITIMER_REAL, duration, 0)
                return func(*args, **kwargs)
            except exception:
                if error_message is not None:
                    raise exception(error_message)
                else:
                    raise exception("{name} function call timed out!".format(
                        name=func.__name__))
            finally:
                signal.alarm(0)
        return func_wrapper
    return interrupt_decorator


def get_ip_address(interfaces):
    """
    Determine the IP address of a given interface.

    Uses the Linux SIOCGIFADDR ioctl to find the IP address associated with a
    network interface, given the name of that interface, e.g. "eth0". The
    address is returned as a string containing a dotted quad.

    This is useful, for instance, when initializing a server.

    The code is based on an ActiveState Code Recipe. [1]_

    Parameters
    ----------
    interfaces : str or list of str
        The name or names of the interfaces to be checked. The function goes
        through each item in the list in order.

    Returns
    -------
    str
        The first hit with a local IP address.

    Raises
    ------
    OSError
        If the interface cannot be found.

    References
    ----------
    .. [1] Paul Cannon, ActiveState Code. "get the IP address associated with
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
    if isinstance(interfaces, list):
        packed = struct.pack("256s", str.encode(interfaces[0]))
    else:
        packed = struct.pack("256s", str.encode(interfaces))
    try:
        address = socket.inet_ntoa(fcntl.ioctl(s.fileno(),
                                               0x8915,  # SIOCGIFADDR
                                               packed)[20:24])
        return address
    except OSError:
        if isinstance(interfaces, list) and len(interfaces) > 1:
            return get_ip_address(interfaces[1:])
        else:
            raise
    finally:
        s.close()
