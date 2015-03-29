# (C) 2015  Kyoto University Mechatronics Laboratory
# Released under the GNU General Public License, version 3
import logging
import math
import sys

from yozakura.rpi.devices import IMU


def main():
    imu_front = IMU("front", address=0x68)
    imu_rear = IMU("rear", address=0x69)

    while True:
        front = [math.degrees(i) for i in imu_front.rpy]
        rear = [math.degrees(i) for i in imu_rear.rpy]
        print("({fr:6.3f}  {fp:6.3f}  {fy:6.3f})  \
               ({rr:6.3f}  {rp:6.3f}  {ry:6.3f})"
               .format(fr=front[0], fp=front[1], fy=front[2],
                       rr=rear[0], rp=rear[1], ry=rear[2]),
              end="\r")


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)

    try:
        main()
    except KeyboardInterrupt:
        print()
        sys.exit(0)
