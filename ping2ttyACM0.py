import serial

s = serial.Serial("/dev/ttyACM0", 38400)
s.write(bytes([7]))
try:
    print(s.read(s.inWaiting()).decode())
finally:
    s.close()
