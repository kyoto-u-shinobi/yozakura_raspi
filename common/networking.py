# (C) 2015  Kyoto University Mechatronics Laboratory
# Released under the GNU General Public License, version 3
"""
Provide networking functions for the base station and the Raspberry Pi.

"""
import fcntl
import socket
import struct


def get_ip_address(interface):
    """
    Determine the IP address of a given interface.

    Uses the Linux SIOCGIFADDR ioctl to find the IP address associated with a
    network interface, given the name of that interface, e.g. "eth0". The
    address is returned as a string containing a dotted quad.

    This is useful, for instance, when initializing a server.

    The code is based on an ActiveState Code Recipe. [1]_

    Parameters
    ----------
    interface : str
        The name of the interface to be used.

    Returns
    -------
    str
        The local IP address.

    Raises
    ------
    OSError
        When the interface cannot be found.

    References
    ----------
    .. [1] Paul Cannon, ActiveState Code. "get the IP address associated with
           a network interface (linux only)"
           http://code.activestate.com/recipes/439094-get-the-ip-address-associated-with-a-network-inter/

    Examples
    --------
    Get the IP address of the device's ``wlan0`` interface.

    >>> get_ip_address("wlan0")
    '192.168.11.2

    """
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    packed = struct.pack("256s", str.encode(interface))
    return socket.inet_ntoa(fcntl.ioctl(s.fileno(),
                                        0x8915,  # SIOCGIFADDR
                                        packed)[20:24])