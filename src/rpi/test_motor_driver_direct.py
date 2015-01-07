import time
import RPi.GPIO as GPIO
import math
GPIO.setmode(GPIO.BOARD)
chan_list = (31, 12, 35)  # 31 is for EN, 12 is for PWMP, 35 is for PWMN
for channel in chan_list:
    GPIO.setup(channel, GPIO.OUT)

# Reverse
def test_reverse():
    print("Going in reverse")
    GPIO.output(31, GPIO.HIGH)
    GPIO.output(12, GPIO.LOW)
    p = GPIO.PWM(35, 28000)  # channel=35 frequency=50Hz
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
    GPIO.output(31, GPIO.HIGH)
    GPIO.output(35, GPIO.LOW)
    p = GPIO.PWM(12, 28000)  # channel=12 frequency=50Hz
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
    GPIO.output(35, GPIO.LOW)
    GPIO.output(12, GPIO.LOW)
    GPIO.output(31, GPIO.LOW)
    GPIO.cleanup()
    print("All done.")

try:
    test_reverse()
    test_forward()
except KeyboardIntterupt:
    pass
finally:
    turn_off()
