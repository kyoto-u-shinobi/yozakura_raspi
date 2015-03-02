# (C) 2015  Kyoto University Mechatronics Laboratory
# Released under the GNU General Public License, version 3
"""
Modules for the Raspberry Pi.

The Raspberry Pi is on the robot. It communicates with:

    - the base station via a Contec router attached by Ethernet
    - an mbed connected via USB
    - various devices connected via I2C

The Raspberry Pi's client module receives speed commands from the base station,
and relays them to the mbed. Its server module receives requests for data from
the connected i2c devices, which it then queries. Finally, it relays back that
data, along with flipper position data acquired from the mbed.

"""
