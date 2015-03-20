# (C) 2015  Kyoto University Mechatronics Laboratory
# Released under the GNU General Public License, version 3
"""
Modules for the base station.

The base station receives a request for speed data from the Raspberry Pi. It
then reads the input state from a controller, calculates the required speeds,
and forwards them to the Raspberry Pi.

In addition, the base station will receive data from a UDP server running on
the Raspberry Pi, which is used by the ROS GUI. It can also request data from
I2C devices attached to the Raspberry Pi.

"""
