# (C) 2015  Kyoto University Mechatronics Laboratory
# Released under the GNU General Public License, version 3
from rpi import motors
import logging


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    left_motor = motors.Motor(12, 8, 10, 11, "left_motor"，hard=True, scaling=0.9)
    right_motor = motors.Motor(35, 32, 36, 38, "right_motor", hard=True, scaling=0.9)

    while True:
        try:
            left_motor.drive(0.5)
            right_motor.drive(0.5)
        except KeyboardInterrupt:
            break
    motors.Motor.shut_down_all()
