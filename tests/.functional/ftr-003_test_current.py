# (C) 2015  Kyoto University Mechatronics Laboratory
# Released under the GNU General Public License, version 3
import logging
import sys

from rpi.devices import CurrentSensor


def main():
    upper_sensor = CurrentSensor(0x40, name="upper current sensor")
    lower_sensor = CurrentSensor(0x44, name="lower current sensor")
    upper_sensor.calibrate(2.6)
    lower_sensor.calibrate(2.6)
    print("Upper Sensor                         Lower Sensor")
    print("="*64)
    while True:
        upper_current = upper_sensor.get_measurement("current")
        upper_power = upper_sensor.get_measurement("power")
        upper_voltage = upper_power / upper_current
        print_upper = "{:5.3f} A, ".format(upper_current) + \
                      "{:6.3f} W, ".format(upper_power) + \
                      "{:6.3f} V".format(upper_voltage)

        lower_current = lower_sensor.get_measurement("current")
        lower_power = lower_sensor.get_measurement("power")
        lower_voltage = lower_power / lower_current
        print_lower = "{:5.3f} A, ".format(lower_current) + \
                      "{:6.3f} W, ".format(lower_power) + \
                      "{:6.3f} V".format(lower_voltage)

        print("{}          {}".format(print_upper, print_lower), end="\r")


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)

    try:
        main()
    except KeyboardInterrupt:
        print()
        sys.exit(0)
