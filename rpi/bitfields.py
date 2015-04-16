# (C) 2015  Kyoto University Mechatronics Laboratory
# Released under the GNU General Public License, version 3
"""
Provide bitfields for Yozakura.

A bitfield is a structure used to store neighbouring bits where each set of
bits, and individual bits, can be addressed. Yozakura uses them to represent
flags, or a packed bit.

These bitfields typically fit into either a single byte, or a word. They allow
easy-to-use bit manipulation, and help prevent manipulation mistakes.

In Yozakura, we use both the structures holding the named bits themselves, as
well as unions which allow us to address the full byte or word at one time.
This makes it easy to store data simultaneously, or to transmit it.

The structure needs _fields_ to be filled as a list of 2-tuples containing
the field name and the type. Optionally, you can add a third entry to the
tuple containing the number of bits to be used.

Examples
--------
These examples use MotorPacket, defined below, to illustrate how bitfields
work, and to compare them to bit manipulation, which you might already know.

Move motor 1 (0b01) in reverse at a speed of 16/31 of full speed. The
resulting byte should contain ``0b01110000``, which has an ascii value of
"p".

>>> packet = MotorPacket()
>>> packet.motor_id = 1
>>> packet.negative = 1
>>> packet.speed = 16
>>> chr(packet.as_byte)
'p'
>>> # Get each item separately.
>>> packet.motor_id
1
>>> packet.negative
1
>>> packet.speed
16

Since the size of the fields were defined in ``MotorPacketBits`` above,
we can set each portio individually without needing to perform bit
manipulation. What we did is the equivalent of:

>>> motor_id = 1 << 6
>>> negative = 1 << 5
>>> speed = 16
>>> packet = motor_id + negative + speed
>>> chr(packet)
'p'
>>> # Get each item separately.
>>> packet >> 6  # motor_id
1
>>> (packet >> 5) & (1 << 0)  # negative
1
>>> packet & 0b11111  # speed
16

"""
import ctypes


# Used in rpi.motors
class MotorPacketBits(ctypes.LittleEndianStructure):
    """
    The bits for the packet sent to the motors.

    Note that the mbed's processor is little endian, which is why a
    ``LittleEndianStructure`` is used.

    See Also
    --------
    MotorPacket

    """
    _fields_ = [("motor_id", ctypes.c_uint8, 2),
                ("negative", ctypes.c_uint8, 1),
                ("speed", ctypes.c_uint8, 5)]


class MotorPacket(ctypes.Union):
    """
    The packet sent to the motors.

    When the Raspberry Pi is connected to the mbed, motor control information
    is encoded as a single byte.

    Using a union allows us to transmit the full byte to the mbed by using
    ``packet.as_byte``, and ensures that it would be exactly eight bits long.

    Attributes
    ----------
    motor_id : 2 bits
        The motor ID. Can range between 0 and 3.
    negative : bool
        Whether the speed is negative.
    speed : 5 bits
        The magnitude of the speed. Can range between 0 and 31.

    Notes
    -----
    Anonymous usage is the bitfield, ``b``. The full byte can be accessed via
    ``as_byte``.

    """
    _fields_ = [("b", MotorPacketBits),
                ("as_byte", ctypes.c_uint8)]

    _anonymous_ = ("b")


# Used in rpi.devices.CurrentSensor
class CurrentConfigurationBits(ctypes.Structure):
    """
    The bits for the configuration register of the INA226 ``CurrentSensor``.

    See Also
    --------
    CurrentConfiguration

    """
    _fields_ = [("reset", ctypes.c_uint16, 1),     # Reset bit
                ("empty", ctypes.c_uint16, 3),
                ("avg", ctypes.c_uint16, 3),       # Averaging mode
                ("bus_ct", ctypes.c_uint16, 3),    # Bus voltage conv. time
                ("shunt_ct", ctypes.c_uint16, 3),  # Shunt voltage conv. time
                ("mode", ctypes.c_uint16, 3)]      # Operating mode


class CurrentConfiguration(ctypes.Union):
    """
    The union for the configuration register of ``CurrentSensor``.

    The current sensor used here is the Texas Instruments INA226 Current/Power
    Monitor. The configuration register details are shown on pages 18 and 19
    of the datasheet. [#]_

    The Configuration Register settings control the operating modes for the
    INA226. This register controls the conversion time settings for both the
    shunt and bus voltage measurements as well as the averaging mode used. The
    operating mode that controls what signals are selected to be measured is
    also programmed in the Configuration Register.

    The Configuration Register can be read from at any time without impacting
    or affecting the device settings or a conversion in progress. Writing to
    the Configuration Register will halt any conversion in progress until the
    write sequence is completed resulting in a new conversion starting based
    on the new contents of the Configuration Register. This prevents any
    uncertainty in the conditions used for the next completed conversion.

    Attributes
    ----------
    reset : bool
        Whether to reset.
    empty : 3 bits
        Not used.
    avg : 3 bits
        Averaging mode. Can range between 0 and 7.
    bus_ct : 3 bits
        Bus voltage conversion time. Can range between 0 and 7.
    shunt_ct : 3 bits
        Shunt voltage conversion time. Can range between 0 and 7.
    mode : 3 bits
        Operating mode. Can range between 0 and 7.

    Notes
    -----
    Anonymous usage is the bitfield, ``b``. The full byte can be accessed via
    ``as_byte``.

    References
    ----------
    .. [#] Texas Instruments, INA 226 datasheet.
           http://www.ti.com/lit/ds/symlink/ina226.pdf

    """
    _fields_ = [("b", CurrentConfigurationBits),
                ("as_byte", ctypes.c_uint16)]

    _anonymous_ = ("b")


class CurrentAlertsFlags(ctypes.Structure):
    """
    The bits for the Mask/Enable register of the INA226 ``CurrentSensor``.

    See Also
    --------
    CurrentAlerts

    """
    _fields_ = [("shunt_ol", ctypes.c_uint16, 1),    # Shunt overvolt
                ("shunt_ul", ctypes.c_uint16, 1),    # Shunt undervolt
                ("bus_ol", ctypes.c_uint16, 1),      # Bus overvolt
                ("bus_ul", ctypes.c_uint16, 1),      # Bus undervolt
                ("power_ol", ctypes.c_uint16, 1),    # Power over limit
                ("conv_watch", ctypes.c_uint16, 1),  # Conversion ready
                ("empty", ctypes.c_uint16, 5),
                ("alert_func", ctypes.c_uint16, 1),  # Alert function flag
                ("conv_flag", ctypes.c_uint16, 1),   # Conversion ready flag
                ("overflow", ctypes.c_uint16, 1),    # Math overflow flag
                ("invert", ctypes.c_uint16, 1),      # Alert polarity bit
                ("latch", ctypes.c_uint16, 1)]       # Alert latch enable


class CurrentAlerts(ctypes.Union):
    """
    The union for the Mask/Enable register of ``CurrentSensor``.

    The current sensor used here is the Texas Instruments INA226 Current/Power
    Monitor. The Mask/Enable register details are shown on pages 21 and 22 of
    the datasheet. [#]_

    The Mask/Enable Register selects the function that is enabled to control
    the Alert pin, as well as how that pin functions. If multiple functions
    are enabled, the highest significant bit position Alert Function (D11-D15)
    takes priority and responds to the Alert Limit register.

    Attributes
    ----------
    shunt_ol : bool
        Whether to trigger an alert when the shunt voltage goes over the limit.
    shunt_ul : bool
        Whether to trigger an alert when the shunt voltage goes below the
        limit.
    bus_ol : bool
        Whether to trigger an alert when the bus voltage goes over the limit.
    bus_ul : bool
        Whether to trigger an alert when the bus voltage goes under the limit.
    power_ol : bool
        Whether to trigger an alert when the power goes over the limit.
    conv_watch : bool
        Whether to trigger an alert when a conversion is ready.
    empty : 5 bits
        Not used.
    alert_func : bool
        Whether the alert was triggered by an alert function.
        (``shunt_ol``, ``shunt_ul``, ``bus_ol``, ``bus_ul``, ``power_ol``)
    conv_flag : bool
        Whether the alert was triggered by a conversion becoming ready.
    overflow : bool
        Whether the alert was triggered by a math overflow.
    invert : bool
        Whether to invert the alert polarity. Default is ``False``. If
        ``True``, the alert line would be ``HIGH`` when active.
    latch : bool
        Whether to latch the alert and flag bits, even after the fault has
        cleared. Default is ``False``.

    Notes
    -----
    Anonymous usage is the bitfield, ``b``. The full byte can be accessed via
    ``as_byte``.

    References
    ----------
    .. [#] Texas Instruments, INA226 datasheet.
            http://www.ti.com/lit/ds/symlink/ina226.pdf

    """
    _fields_ = [("b", CurrentAlertsFlags),
                ("as_byte", ctypes.c_uint16)]

    _anonymous_ = ("b")
