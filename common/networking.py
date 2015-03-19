# (C) 2015  Kyoto University Mechatronics Laboratory
# Released under the GNU General Public License, version 3
"""
Provide networking functions for the base station and the Raspberry Pi.

This module provides primitives for TCP and UDP clients and servers, and also
provides a function to determine the IP address of an interface.

"""
import abc
import fcntl
import logging
import socket
import socketserver
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
        Could not find the interface.

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


class Communication(object):
    def receive(self, *args, **kwargs):
        """
        Receive a message from the server.
        
        Parameters
        ----------
        size : int
            The number of bytes to receive.

        Returns
        -------
        bytecode
            The data received.

        """
        return self.request.recv(*args, **kwargs)


class TCPCommunication(Communication):
    def send(self, message):
        """
        Send a message to the server.

        Parameters
        ----------
        message : str
            The message to send to the server.

        """
        try:
            self.request.sendall(str.encode(message))
        except TypeError:  # Already bytecode
            self.request.sendall(message)


class UDPCommunication(Communication):
    def send(self, message, address):
        """
        Send a message to the server.

        Parameters
        ----------
        message : str
            The message to send to the server.
        address : 2-tuple of (str, int)
            The address to which to send the message

        """
        try:
            self.request.sendto(str.encode(message), address)
        except TypeError:  # Already bytecode
            self.request.sendto(message, address)


class HandlerBase(socketserver.BaseRequestHandler):
    """A logging base request handler."""
    def __init__(self, request, client_address, server):
        """
        Inits the handler.

        This method gets called by the server automatically.

        """
        self.logger = logging.getLogger("{}_handler".format(client_address[0]))
        self.logger.debug("New handler created")
        super().__init__(request, client_address, server)


class TCPHandlerBase(HandlerBase, TCPCommunication):
    pass


class UDPHandlerBase(HandlerBase, UDPCommunication):
    pass


class LoggingForkingMixinServer(socketserver.ForkingMixIn):
    """
    A logging, forking server.

    Parameters
    ----------
    server_address : 2-tuple of (str, int)
        The address at which the server is listening. The elements are the
        server address and the port number respectively.
    handler_class : Handler
        The request handler. Each new request generates a separate process
        running that handler.
    
    Examples
    --------
    >>> server = TCPServerBase(("192.168.11.1", 22), Handler)
    
    """
    allow_reuse_address = True  # Can resume immediately after shutdown

    def __init__(self, server_address, handler_class):
        self.logger = logging.getLogger("{}_server".format(server_address[0]))
        self.logger.debug("Creating server")
        super().__init__(server_address, handler_class)
        self.logger.info("Listening to port {}".format(server_address[1]))

    def serve_forever(self, *args, **kwargs):
        """Handle requests until an explicit ``shutdown()`` request."""
        self.logger.info("Server started")
        super().serve_forever(*args, **kwargs)


class TCPServerBase(LoggingForkingMixinServer, socketserver.TCPServer):
    pass


class UDPServerBase(LoggingForkingMixinServer, socketserver.UDPServer):
    pass


class ClientBase(Object):
    """
    A Client base.
    
    Parameters
    ----------
    server_address : 2-tuple of (str, int)
        The address at which the server is listening. The elements are the
        server address and the port number respectively.

    Attributes
    ----------
    request : socket
        Handles communication with the server.

    """
    def __init__(self, server_address):
        # Get local IP address.
        try:
            ip_address = get_ip_address("eth0")
        except OSError:
            ip_address = get_ip_address("enp2s0")

        self.logger = logging.getLogger("{}_client".format(ip_address))
        self.logger.debug("Creating client")
    
    @abc.abstractmethod
    def run(self):
        """
        Keep sending requests until a ``KeyboardInterrupt`` is received.

        Subclasses must implement this method.
        """
        pass

    def shutdown(self):
        """Shut down the client."""
        self.logger.debug("Shutting down client")
        self.request.close()
        self.logger.info("Client shut down")
        

class TCPClientBase(ClientBase, TCPCommunication):
    """
    A TCPClient base.

    Parameters
    ----------
    server_address : 2-tuple of (str, int)
        The address at which the server is listening. The elements are the
        server address and the port number respectively.

    Attributes
    ----------
    request : socket
        Handles communication with the server.

    Examples
    --------
    >>> client = TCPClientBase(("192.168.11.1", 22))

    """
    def __init__(self, server_address):
        super().__init__(server_address)
        self.request = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.request.connect(server_address)
        self.logger.info("Connected to {}:{}".format(server_address[0],
                                                     server_address[1]))


class UDPClientBase(ClientBase, UDPCommunication):
    """
    A UDP client base.

    Parameters
    ----------
    server_address : 2-tuple of (str, int)
        The address at which the server is listening. The elements are the
        server address and the port number respectively.

    Attributes
    ----------
    request : socket
        Handles communication with the server.

    Examples
    --------
    >>> client = UDPClientBase(("192.168.11.1", 22))

    """
    def __init__(self, server_address):
        super().__init__(server_address)
        self.server_address = server_address
        self.request = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.logger.info("Listening to {}:{}".format(server_address[0],
                                                     server_address[1]))
