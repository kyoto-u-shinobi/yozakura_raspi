import time
import RPi.GPIO as GPIO
import math
GPIO.setmode(GPIO.BOARD)
chan_list = (11, 13, 15)  # 11 is for EN, 13 is for PWMP, 15 is for PWMN
for channel in chan_list:
    GPIO.setup(channel, GPIO.OUT)

# Reverse
def test_reverse():
    print("Going in reverse")
    GPIO.output(11, GPIO.HIGH)
    GPIO.output(13, GPIO.LOW)
    p = GPIO.PWM(15, 50)  # channel=15 frequency=50Hz
    p.start(0)
    p.ChangeDutyCycle(0)
    print("Motor off for one second")
    time.sleep(1)
    p.ChangeDutyCycle(10)
    print("Motor at 10% for four seconds")
    time.sleep(4)
    p.ChangeDutyCycle(100)
    print("Motor at 100% for four seconds")
    time.sleep(4)
    p.stop()
    print("Motor off.")

# Forward
def test_forward():
    print("Going Forward")
    GPIO.output(11, GPIO.HIGH)
    GPIO.output(15, GPIO.LOW)
    p = GPIO.PWM(13, 50)  # channel=13 frequency=50Hz
    p.start(0)
    p.ChangeDutyCycle(0)
    print("Motor off for one second.")
    time.sleep(1)
    p.ChangeDutyCycle(20)
    print("Motor at 20% for four seconds.")
    time.sleep(4)
    p.ChangeDutyCycle(100)
    print("Motor at 100% for four seconds")
    time.sleep(4)
    p.stop()
    print("Motor off.")

# Off
def turn_off():
    print("Turning off.")
    GPIO.output(15, GPIO.LOW)
    GPIO.output(13, GPIO.LOW)
    GPIO.output(11, GPIO.LOW)
    GPIO.cleanup()
    print("All done.")

test_reverse()
test_forward()
turn_off()
