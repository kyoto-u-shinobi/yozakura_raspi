# (C) 2015  Kyoto University Mechatronics Laboratory
# Released under the GNU General Public License, version 3
"""
Common datatypes used throughout Yozakura.

"""
from collections import namedtuple


CurrentSensorData = namedtuple("CurrentSensorData", "current power voltage")
IMUData = namedtuple("IMUData", "roll pitch yaw")
