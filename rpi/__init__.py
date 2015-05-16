# (C) 2015  Kyoto University Mechatronics Laboratory
# Released under the GNU General Public License, version 3
"""
Modules for the Raspberry Pi.

The Raspberry Pi is on the Yozakura. It communicates with:

- the base station via a Contec router attached by an Ethernet cable
- two mbed microcontrollers connected via USB
- various devices connected via I2C

The Raspberry Pi's client module receives speed commands from the base station,
and relays them to the mbeds to control the motors and arm. In addition, it
sends back data about flipper positions, current sensor measurements, pose
information, arm position and status, temperature measurements, and CO2
readings.

"""
