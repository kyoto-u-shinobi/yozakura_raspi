import serial
import time

print("Connecting to /dev/ttyACM0...", end="\r")
try:
    s = serial.Serial("/dev/ttyACM0", 38400)
    s.write(bytes([7]))
    time.sleep(1)
    print("The mbed at /dev/ttyACM0 says: " + s.read(s.inWaiting()).decode())
except serial.SerialException:
    print("No mbed connected to /dev/ttyACM0")
finally:
    try:
        s.close()
    except NameError:
        pass

print("Connecting to /dev/ttyACM1...", end="\r")
try:
    s = serial.Serial("/dev/ttyACM1", 38400)
    s.write(bytes([7]))
    time.sleep(1)
    print("The mbed at /dev/ttyACM1 says: " + s.read(s.inWaiting()).decode())
except serial.SerialException:
    print("No mbed connected to /dev/ttyACM1")
finally:
    try:
        s.close()
    except NameError:
        pass

print("Connecting to /dev/ttyACM2...", end="\r")
try:
    s = serial.Serial("/dev/ttyACM2", 38400)
    s.write(bytes([7]))
    time.sleep(1)
    print("The mbed at /dev/ttyACM2 says: " + s.read(s.inWaiting()).decode())
except serial.SerialException:
    print("No mbed connected to /dev/ttyACM2")
finally:
    try:
        s.close()
    except NameError:
        pass

print("Connecting to /dev/ttyACM3...", end="\r")
try:
    s = serial.Serial("/dev/ttyACM3", 38400)
    s.write(bytes([7]))
    time.sleep(1)
    print("The mbed at /dev/ttyACM3 says: " + s.read(s.inWaiting()).decode())
except serial.SerialException:
    print("No mbed connected to /dev/ttyACM3")
finally:
    try:
        s.close()
    except NameError:
        pass
