# (C) 2015  Kyoto University Mechatronics Laboratory
# Released under the GNU General Public License, version 3
import logging
import math
import sys

from rpi.devices import IMU


def main():
    imu_front = IMU("Front", address=0x68)
    imu_rear = IMU("Rear", address=0x69)

    while True:
        logging.debug("{}  {}".format([math.degrees(i) for i in imu_front.rpy],
            [math.degrees(i) for i in imu_rear.rpy]))


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)

    try:
        main()
    except KeyboardInterrupt:
        sys.exit(0)
