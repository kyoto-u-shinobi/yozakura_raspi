# (C) 2015  Kyoto University Mechatronics Laboratory
# Released under the GNU General Public License, version 3
import logging
import serial
import sys

from rpi.motor import Motor


def main():
    mbed = serial.Serial("/dev/ttyACM0", 38400)
    motor = Motor("motor", 8, 10, 7)
    motor.enable_serial(mbed)

    speed = 0

    while True:
        button = input("Press:\n" +
                       "a to increase speed,\n" +
                       "z to decrease speed\n" +
                       "q to stop\n" +
                       "r to reset: ")
        if button == "a":
            if speed <= 1:
                speed += 0.05
        elif button == "A":
            speed = 1
        elif button == "z":
            if speed >= -1:
                speed -= 0.05
        elif button == "Z":
            speed = -1
        elif button.lower() == "q":
            speed = 0
        elif button.lower() == "r":
            motor.reset_driver()

        print("Speed: {}".format(speed))
        motor.drive(speed)
        try:
            positions = mbed.readline().split()
            *_, lpos, rpos = [int(i, 0) / 0xFFFF for i in positions]
            print("Flippers: {:6.3f}  {:6.3f}".format(lpos, rpos))
        except ValueError:
            pass


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)

    try:
        main()
    except KeyboardInterrupt:
        Motor.shutdown_all()
        mbed.close()
        sys.exit(0)
