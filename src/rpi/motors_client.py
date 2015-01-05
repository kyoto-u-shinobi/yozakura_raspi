# (C) 2015  Kyoto University Mechatronics Laboratory
# Released under the GNU General Public License, version 3
import motors
import socket
import pickle
import logging


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    soft_motor = motors.Motor(31, 12, 35, 37, "soft_motor", hard=False)
    #hard_motor = motors.Motor(31, 12, 35, 37, "hard_motor", hard=True)
    #right_motor = motors.Motor(32, 36, 38, 40, "right_motor")

    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect(("10.249.255.151", 9000))

    while True:
        try:
            s.sendall(str.encode("sticks_y"))
            result = s.recv(1024)
            lstick_y, rstick_y = pickle.loads(result)
            logging.info("{:9.7} {:9.7}".format(lstick_y, rstick_y))
            soft_motor.drive(-lstick_y)
            #if not lstick_y:
                #hard_motor.drive(-rstick_y)
        except KeyboardInterrupt:
            break
    motors.Motor.shut_down_all()
    s.close()
