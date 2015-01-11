import serial
import tt

ser = serial.Serial("/dev/ttyACM0", 9600)
time.sleep(2)
for num in range(6):
    ser.write(str.encode("a"))
    time.sleep(1)
ser.close()
