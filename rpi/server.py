# (C) 2015 Kyoto University Mechatronics Laboratory
# Released under the GNU General Public License, version 3
"""
UDP server for sensor data.

"""
import logging
import serial
import pickle
import socket

from common.networking import UDPServerBase, UDPHandlerBase

class MyUDPHandler(socketserver.BaseRequestHandler):
    """
    Handler
    
    """
    def handle(self):
        self.logger.info("Connected to client")
        socket = self.request[1]
        while True:
            mytime = time.time()
            self.server.time = mytime
            self.server.test.time = mytime
            socket.sendto(str.encode(str(mytime)), self.client_address)
            time.sleep(1)
