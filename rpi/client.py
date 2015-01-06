# (C) 2015  Kyoto University Mechatronics Laboratory
# Released under the GNU General Public License, version 3
from rpi.motors import Motor
import socket
import pickle
import logging


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    left_motor = Motor(12, 8, 10, 11, "left_motor", hard=True, scaling=0.9)
    right_motor = Motor(35, 32, 36, 38, "right_motor", hard=True, scaling=0.9)

    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    #s.connect(("192.168.54.125", 9999))
    s.connect(("10.249.255.202", 9999))
    while True:
        try:
            s.sendall(str.encode("body_sticks_y"))
            result = s.recv(1024)
            lstick_y, rstick_y = pickle.loads(result)
            logging.debug("{:9.7} {:9.7}".format(lstick_y, rstick_y))
            left_motor.drive(-lstick_y)
            right_motor.drive(-rstick_y)
        except (KeyboardInterrupt, RuntimeError):
            break
    if not Motor.fault:
        Motor.shut_down_all()
    s.close()
