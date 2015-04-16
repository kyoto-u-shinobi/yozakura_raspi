# (C) 2015  Kyoto University Mechatronics Laboratory
# Released under the GNU General Public License, version 3
"""
Common datatypes used throughout Yozakura.

"""
from collections import namedtuple


SpeedCmd_ = namedtuple("SpeedCmd", "lwheel rwheel lflipper rflipper")
class SpeedCmd(SpeedCmd_):
    """
    A container for the speed commands sent to the motors.

    Attributes
    ----------
    lwheel : float
        The speed of the left wheel. Ranges from -1 to 1.
    rwheel : float
        The speed of the right wheel. Ranges from -1 to 1.
    lflipper : int
        The direction of the left flipper. Can be 0, -1, or 1.
    rflipper : int
        The direction of the right flipper. Can be 0, -1, or 1.

    """


ArmCmd_ = namedtuple("ArmCmd", "mode yaw pitch extend")
class ArmCmd(ArmCmd_):
    """
    A container for the commands sent to the arm.

    Attributes
    ----------
    mode : int
        The operating mode of the arm. Can be 0, 1, or 2.
    yaw : int
        The direction of the yaw servo. Can be 0, -1, or 1.
    pitch : int
        The direction of the pitch servo. Can be 0, -1, or 1.
    extend : int
        The direction of the prismatic joint. Can be 0, -1, or 1.

    """


FlipperPositions_ = namedtuple("FlipperPositions", "current power voltage")
class FlipperPositions(FlipperPositions_):
    """
    A container for the flipper position.

    Attributes
    ----------
    left : float
        The left flipper position. Ranges from 0 to 1.
    right : float
        The right flipper position. Ranges from 0 to 1.

    """


CurrentSensorData_ = namedtuple("CurrentSensorData", "current power voltage")
class CurrentSensorData(CurrentSensorData_):
    """
    A container for the current sensor data.

    Attributes
    ----------
    current : float
        The current, in Amperes.
    power : float
        The power, in Watts.
    voltage : float
        The voltage, in Volts.

    """

IMUData_ = namedtuple("IMUData", "roll pitch yaw")
class IMUData(IMUData_):
    """
    A container for the IMU data.

    Attributes
    ----------
    roll  : float
        The roll, in radians.
    pitch : float
        The pitch, in radians.
    yaw : float
        The yaw, in radians.

    """
