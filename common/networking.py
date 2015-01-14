# (C) 2015  Kyoto University Mechatronics Laboratory
# Released under the GNU General Public License, version 3
import abc
import logging
import socketserver
import socket
import fcntl
import struct


def get_ip_address(interface):
    """http://goo.gl/zdkOeZ"""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    packed = struct.pack("256s", str.encode(interface))
    return socket.inet_ntoa(fcntl.ioctl(s.fileno(),
                                        0x8915,  # SIOCGIFADDR
                                        packed)[20:24])


class HandlerBase(socketserver.BaseRequestHandler):
    def __init__(self, request, client_address, server):
        self.logger = logging.getLogger("{}_handler".format(client_address[0]))
        self.logger.debug("New handler created")
        super().__init__(request, client_address, server)


class ServerBase(socketserver.ForkingMixIn, socketserver.TCPServer):
    allow_reuse_address = True
    def __init__(self, server_address, handler_class):
        super().__init__(server_address, handler_class)
        self.logger = logging.getLogger("{}_server".format(self.server_address[0]))
        self.logger.info("Listening to port {}".format(server_address[1]))


class ClientBase(object):
    def __init__(self, server_address):
        try:
            self.ip_address = get_ip_address("eth0")
        except OSError:
            self.ip_address = get_ip_address("enp2s0")
        self.logger = logging.getLogger("{}_client".format(self.ip_address))
        self.request = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.request.connect(server_address)

    def send(self, string):
        try:
            self.request.sendall(str.encode(string))
        except TypeError:  # Already bytecode
            self.request.sendall(string)

    def receive(self, length=1024):
        return self.request.recv(length)

    @abc.abstractmethod
    def run(self):
        pass

    def quit(self):
        self.request.close()
