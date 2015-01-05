# (C) 2015  Kyoto University Mechatronics Laboratory
# Released under the GNU General Public License, version 3
from rpi import motors
import socket
import pickle
import logging


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    left_motor = motors.Motor(12, 33, 35, 37, "left_motor", hard=False)
    right_motor = motors.Motor(32, 38, 36, 40, "right_motor", hard=False)

    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect(("192.168.54.125", 9999))
    while True:
        try:
            s.sendall(str.encode("body_sticks_y"))
            result = s.recv(1024)
            lstick_y, rstick_y = pickle.loads(result)
            logging.debug("{:9.7} {:9.7}".format(lstick_y, rstick_y))
            left_motor.drive(-lstick_y)
            right_motor.drive(-rstick_y)
        except KeyboardInterrupt:
            break
    motors.Motor.shut_down_all()
    s.close()
