# (C) 2015  Kyoto University Mechatronics Laboratory
# Released under the GNU General Public License, version 3
"""
Modules for the Raspberry Pi.

The Raspberry Pi is on the robot. It communicates with:

- the base station via a Contec router attached by Ethernet
- an mbed connected via USB
- various devices connected via I2C

The Raspberry Pi's client module receives speed commands from the base station,
and relays them to the mbed to control the motors. In addition, it sends data
about flipper positions, current sensor measurements, and pose information back
to the base station.

"""
