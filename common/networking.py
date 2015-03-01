# (C) 2015  Kyoto University Mechatronics Laboratory
# Released under the GNU General Public License, version 3
import abc
import fcntl
import logging
import socket
import socketserver
import struct


def get_ip_address(interface):
    """Get the local IP address from the interface name.

    References:
        Code taken from: http://goo.gl/zdkOeZ

    Args:
        interface: The name of the interface to be used.

    Returns:
        The local IP address.

    Raises:
        OSError: Could not find the interface.
    """
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    packed = struct.pack("256s", str.encode(interface))
    return socket.inet_ntoa(fcntl.ioctl(s.fileno(),
                                        0x8915,  # SIOCGIFADDR
                                        packed)[20:24])


class HandlerBase(socketserver.BaseRequestHandler):
    """A logging base request handler."""
    def __init__(self, request, client_address, server):
        """Inits the handler. Called by the server."""
        self.logger = logging.getLogger("{}_handler".format(client_address[0]))
        self.logger.debug("New handler created")
        super().__init__(request, client_address, server)


class TCPServerBase(socketserver.ForkingMixIn, socketserver.TCPServer):
    """A logging, forking TCP server."""
    allow_reuse_address = True
    def __init__(self, server_address, handler_class):
        """Inits the server.

        Args:
            server_address: The address on which the server is listening. This
                is a tuple containing a string giving the address, and an
                integer port number.
            handler_class: The request handler. Each new request generates a
                separate process running the handler.
        """
        self.logger = logging.getLogger("{}_server".format(server_address[0]))
        self.logger.debug("Creating server")
        super().__init__(server_address, handler_class)
        self.logger.info("Listening to port {}".format(server_address[1]))

    def serve_forever(self, *args, **kwargs):
        """Handle requests until an explicit shutdown() request."""
        self.logger.info("Server started")
        super().serve_forever(*args, **kwargs)


class UDPServerBase(socketserver.ForkingMixIn, socketserver.UDPServer):
    """A logging, forking UDP server."""
    allow_reuse_address = True
    def __init__(self, server_address, handler_class):
        """Inits the server.

        Args:
            server_address: The address on which the server is listening. This
                is a tuple containing a string giving the address, and an
                integer port number.
            handler_class: The request handler. Each new request generates a
                separate process running the handler.
        """
        self.logger = logging.getLogger("{}_server".format(server_address[0]))
        self.logger.debug("Creating server")
        super().__init__(server_address, handler_class)
        self.logger.info("Listening to port {}".format(server_address[1]))

    def serve_forever(self, *args, **kwargs):
        """Handle requests until an explicit shutdown() request."""
        self.logger.info("Server started")
        super().serve_forever(*args, **kwargs)


class TCPClientBase(object):
    """A TCPclient base.

    Attributes:
        request: Socket object handling communication with the server.
    """
    def __init__(self, server_address):
        """Inits the client

        Args:
            server_address: The address on which the server is listening. This
                is a tuple containing a string giving the address, and an
                integer port number.
        """
        # Get local IP address.
        try:
            ip_address = get_ip_address("eth0")
        except OSError:
            ip_address = get_ip_address("enp2s0")

        self.logger = logging.getLogger("{}_client".format(ip_address))
        self.logger.debug("Creating client")
        self.request = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.request.connect(server_address)
        self.logger.info("Connected to {}:{}".format(server_address[0],
                                                     server_address[1]))

    def send(self, string):
        """Send a string to the server.

        Args:
            string: The string to be sent.
        """
        try:
            self.request.sendall(str.encode(string))
        except TypeError:  # Already bytecode
            self.request.sendall(string)

    def receive(self, *args, **kwargs):
        """Receive a string from the server.

        Returns:
            Bytecode representing the data received.
        """
        return self.request.recv(*args, **kwargs)

    @abc.abstractmethod
    def run(self):
        """Keep sending requests until a KeyboardInterrupt is received.

        Subclasses must implement this method."""
        pass

    def shutdown(self):
        """Shut down the client."""
        self.logger.debug("Shutting down client")
        self.request.close()
        self.logger.info("Client shut down")


class UDPClientBase(object):
    """A UDP client base.

    Attributes:
        request: Socket object handling communication with the server.
        server_address: The address on which the server is listening. This
            is a tuple containing a string giving the address, and an integer
            port number.
    """
    def __init__(self, server_address):
        """Inits the client

        Args:
            server_address: The address on which the server is listening. This
                is a tuple containing a string giving the address, and an
                integer port number.
        """
        # Get local IP address.
        try:
            ip_address = get_ip_address("eth0")
        except OSError:
            ip_address = get_ip_address("enp2s0")

        self.logger = logging.getLogger("{}_client".format(ip_address))
        self.logger.debug("Creating client")
        self.server_address = server_address
        self.request = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.logger.info("Listening to {}:{}".format(server_address[0],
                                                     server_address[1]))

    def send(self, string):
        """Send a string to the server.

        Args:
            string: The string to be sent.
        """
        try:
            self.request.sendto(str.encode(string), self.server_address)
        except TypeError:  # Already bytecode
            self.request.sendto(string, self.server_address)

    def receive(self, *args, **kwargs):
        """Receive a string from the server.

        Returns:
            Bytecode representing the data received.
        """
        return self.request.recv(*args, **kwargs)

    @abc.abstractmethod
    def run(self):
        """Keep sending requests until a KeyboardInterrupt is received.

        Subclasses must implement this method."""
        pass

    def shutdown(self):
        """Shut down the client."""
        self.logger.debug("Shutting down client")
        self.request.close()
        self.logger.info("Client shut down")

