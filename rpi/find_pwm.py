# (C) 2015  Kyoto University Mechatronics Laboratory
# Released under the GNU General Public License, version 3
from rpi import motors
import logging
import time


if __name__ == "__main__":
    logging.basicConfig(level=logging.WARNING)
    try:
        motor = motors.Motor(12, 13, 11, 7, "right_motor", hard=True)
        motor.drive(1)
    except KeyboardInterrupt:
        pass
    finally:
        motors.Motor.shut_down_all()
