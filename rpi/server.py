# (C) 2015 Kyoto University Mechatronics Laboratory
# Released under the GNU General Public License, version 3
"""
UDP server for sensor data.

"""
import logging
import pickle

from common.networking import UDPServerBase, UDPHandlerBase


class Handler(UDPHandlerBase):
    """
    Handler
    
    """
    def handle(self):
        self.logger.info("Connected to client")
        while True:
            sensor_data = self.server.ser.readline().split()
            reply = pickle.dumps(sensor_data)
            self.send(reply, self.client_address)
            time.sleep(self.server.refresh_period)


class Server(UDPServerBase):
    """
    Server
    
    """
    def __init__(self, server_address, handler_class, ser, refresh_period=1):
        super().__init__(server_address, handler_class)
        self.ser = ser
        self.refresh_period = refresh_period  # s
