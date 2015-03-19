# (C) 2015 Kyoto University Mechatronics Laboratory
# Released under the GNU General Public License, version 3
"""
UDP server for sensor data.

"""
import logging
import pickle

from common.networking import UDPClientBase

class Client(UDPClientBase):
    def run(self):
        self.logger.info("Client started")
        
        self.send("\n", self.server_address)
        while True:
            result = self.receive(64)
            self.logger.debug(str(pickle.loads(result)))
