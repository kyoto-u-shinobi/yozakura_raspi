# (C) 2015  Kyoto University Mechatronics Laboratory
# Released under the GNU General Public License, version 3
"""Bitfields are..."""

import ctypes


class MotorPacketBits(ctypes.LittleEndianStructure):
    """The bits for the packet sent to the motors."""
    _fields_ = [("motor_id", ctypes.c_uint8, 2),
                ("negative", ctypes.c_uint8, 1),
                ("speed", ctypes.c_uint8, 5)]


class MotorPacket(ctypes.Union):
    """The packet sent to the motors"""
    _fields_ = [("b", MotorPacketBits),
                ("as_byte", ctypes.c_uint8)]

    _anonymous_ = ("b")


class CurrentConfigurationBits(ctypes.Structure):
    _fields_ = [("reset", ctypes.c_uint16, 1),
                ("upper", ctypes.c_uint16, 3),
                ("avg", ctypes.c_uint16, 3),
                ("bus_ct", ctypes.c_uint16, 3),
                ("shunt_ct", ctypes.c_uint16, 3),
                ("mode", ctypes.c_uint16, 3)]


class CurrentConfiguration(ctypes.Union):
    _fields_ = [("bits", CurrentConfigurationBits),
                ("as_byte", ctypes.c_uint16)]

    _anonymous_ = ("bits")


class CurrentAlertsBits(ctypes.Structure):
    _fields_ = [("shunt_ol", ctypes.c_uint16, 1),
                ("shunt_ul", ctypes.c_uint16, 1),
                ("bus_ol", ctypes.c_uint16, 1),
                ("bus_ul", ctypes.c_uint16, 1),
                ("power_ol", ctypes.c_uint16, 1),
                ("conv_watch", ctypes.c_uint16, 1),
                ("empty", ctypes.c_uint16, 5),
                ("alert_func", ctypes.c_uint16, 1),
                ("conv_flag", ctypes.c_uint16, 1),
                ("overflow", ctypes.c_uint16, 1),
                ("polarity", ctypes.c_uint16, 1),
                ("latch", ctypes.c_uint16, 1)]


class CurrentAlerts(ctypes.Union):
    _fields_ = [("bits", CurrentAlertsBits),
                ("as_byte", ctypes.c_uint16)]

    _anonymous_ = ("bits")


class ADCConfigurationBits(ctypes.Structure):
    _fields_ = [("ready", ctypes.c_uint8, 1),
                ("channel", ctypes.c_uint8, 2),
                ("mode", ctypes.c_uint8, 1),
                ("rate", ctypes.c_uint8, 2),
                ("gain", ctypes.c_uint8, 2)]


class ADCConfiguration(ctypes.Union):
    _fields_ = [("bits", ADCConfigurationBits),
                ("as_byte", ctypes.c_uint8)]

    _anonymous_ = ("bits")

