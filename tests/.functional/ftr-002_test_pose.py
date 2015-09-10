# (C) 2015  Kyoto University Mechatronics Laboratory
# Released under the GNU General Public License, version 3
import logging
import math
import sys

from rpi.devices import IMU


def main():
    imu_front = IMU("front", address=0x68)
    imu_rear = IMU("rear", address=0x69)

    while True:
        front = [math.degrees(i) for i in imu_front.rpy]
        rear = [math.degrees(i) for i in imu_rear.rpy]
        print("({:6.3f}  {:6.3f}  {:6.3f})  ({:6.3f}  {:6.3f}  {:6.3f})".format(front[0], front[1], front[2], rear[0], rear[1], rear[2]), end="\r")


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)

    try:
        main()
    except KeyboardInterrupt:
        print()
        sys.exit(0)
