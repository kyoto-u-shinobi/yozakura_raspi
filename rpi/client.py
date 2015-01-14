# (C) 2015  Kyoto University Mechatronics Laboratory
# Released under the GNU General Public License, version 3
from common.networking import ClientBase
from rpi.motors import Motor
import serial
import time
import socket
import pickle
import logging


class Client(ClientBase):
    def __init__(self, *args):
        super().__init__(*args)
        self.request.settimeout(0.5)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    time_stamp = time.time()

    left_motor = Motor(13, 8, 10, 11, "left_motor", 0, max_speed=0.6)
    right_motor = Motor(12, 36, 32, 38, "right_motor", 1, max_speed=0.6)
    try:
        ser = serial.Serial("/dev/ttyACM0", 9600)
    except serial.SerialException:
        logging.warning("mbed is not connected!")

    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect(("192.168.54.125", 9999))
    #s.connect(("10.249.255.151", 9999))
    s.settimeout(0.5)
    single_stick = False
    while not Motor.fault:
        try:
            s.sendall(str.encode("body"))
            try:
                result = s.recv(1024)
            except socket.timeout:
                logging.warning("Lost connection to operating station")
                logging.info("Turning off motors")
                left_motor.send_byte(0, ser)
                right_motor.send_byte(0, ser)
                continue

            dpad, lstick, rstick, buttons = pickle.loads(result)
            if buttons[8]:  # The select button was pressed
                current_time = time.time()
                if current_time - time_stamp >= 1:
                    if single_stick:
                        single_stick = False
                        logging.info("Control mode switched: Use lstick and rstick to control robot")
                    else:
                        single_stick = True
                        logging.info("Control mode switched: Use lstick to control robot")
                    time_stamp = current_time

            if single_stick:
                logging.debug("lstick: {:9.7} {:9.7}".format(lstick[0], lstick[1]))
            else:
                logging.debug("leftright {:9.7} {:9.7}".format(lstick[1], rstick[1]))

            if single_stick:
                if -0.1 < lstick[1] < 0.1:  # Rotate in place
                    left_motor.send_byte(lstick[0], ser)
                    right_motor.send_byte(-lstick[0], ser)
                else:
                    left_motor.send_byte(-lstick[1] * (1 + lstick[0]) / (1 + abs(lstick[0])), ser)
                    right_motor.send_byte(-lstick[1] * (1 - lstick[0]) / (1 + abs(lstick[0])), ser)
            else:
                left_motor.send_byte(-lstick[1], ser)
                right_motor.send_byte(-rstick[1], ser)

        except (KeyboardInterrupt, RuntimeError):
            break
    Motor.shut_down_all()
    logging.debug("Closing serial port")
    ser.close()
    logging.debug("Client closing")
    s.close()
    logging.debug("Client closed")
