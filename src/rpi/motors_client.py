# (C) 2015  Kyoto University Mechatronics Laboratory
# Released under the GNU General Public License, version 3
import socket
import pickle
from RPi import GPIO as gpio


channels = {"EN": 11, "PWMP": 13, "PWMN": 15}


def gpio_setup():
    gpio.setmode(gpio.BOARD)
    for channel in channels.values():
        gpio.setup(channel, gpio.OUT)
    gpio.output(channels["EN"], gpio.HIGH)


def drive_motor(speed):
    if speed < 0:
        driver_forward.ChangeDutyCycle(0)
        driver_reverse.ChangeDutyCycle(-speed * 100)
    else:
        driver_forward.ChangeDutyCycle(speed * 100)
        driver_reverse.ChangeDutyCycle(0)


def shut_down():
    driver_forward.stop()
    driver_reverse.stop()
    for channel in channels.values():
        gpio.output(channel, gpio.LOW)
    gpio.cleanup()


if __name__ == "__main__":
    gpio_setup()
    driver_forward = gpio.PWM(channels["PWMP"], 50)  # Frequency = 50 Hz
    driver_reverse = gpio.PWM(channels["PWMN"], 50)  # Frequency = 50 Hz
    driver_forward.start(0)
    driver_reverse.start(0)
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect(("10.249.255.151", 9000))
    data = "sticks_y"
    while True:
        try:
            s.sendall(data.encode())
            result = s.recv(1024)
            lstick_y, rstick_y = pickle.loads(result)
            drive_motor(-lstick_y)
        except KeyboardInterrupt:
            break
    s.close()
    shut_down()
