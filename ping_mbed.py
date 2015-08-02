# (C) 2015  Kyoto University Mechatronics Laboratory
# Released under the GNU General Public License, version 3
"""
A script to check for the identities and locations of any connected mbeds.

This script usually needs to be run with superuser privileges.

"""
import serial
import time

for i in range(4):
    device = "/dev/ttyACM{n}".format(n=i)
    print("Connecting to {dev}...".format(dev=device), end="\r")
    try:
        s = serial.Serial(device, 38400)
        s.write(bytes([7]))  # mbed ID request
        time.sleep(1)
        reply = s.read(s.inWaiting()).decode()
        print("The mbed at {dev} says: {reply}".format(dev=device, reply=reply))
    except serial.SerialException:
        print("No mbed connected to {dev}".format(dev=device))
    finally:
        try:
            s.close()
        except NameError:
            pass