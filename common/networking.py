# (C) 2015  Kyoto University Mechatronics Laboratory
# Released under the GNU General Public License, version 3
"""
Provide a method to determine the current IP address.

"""
import fcntl
import socket
import struct


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
