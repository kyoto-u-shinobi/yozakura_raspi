# (C) 2015  Kyoto University Mechatronics Laboratory
# Released under the GNU General Public License, version 3
import logging
import serial

from rpi.motor import Motor


def main():
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

        logging.debug("Speed: {}".format(speed))
        motor.drive(speed)
        try:
            positions = mbed.readline().split()
            *_, lpos, rpos = [int(i, 0) / 0xFFFF for i in positions]
            logging.debug("Flippers: {:6.3f}  {:6.3f}".format(lpos, rpos))
        except ValueError:
            pass


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)

    mbed = serial.Serial("/dev/ttyACM0", 9600)
    motor = Motor("motor", 11, 12, 13)
    motor.enable_serial(mbed)

    try:
        main()
    except KeyboardInterrupt:
        pass
    finally:
        Motor.shutdown_all()
        mbed.close()
