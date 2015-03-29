# (C) 2015  Kyoto University Mechatronics Laboratory
# Released under the GNU General Public License, version 3
import logging
import sys

from yozakura.rpi.devices import CurrentSensor


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
        print_upper = "{ui:5.3f} A, {up:6.3f} W, {uv:6.3f} V".format(
            ui=upper_current, up=upper_power, uv=upper_voltage)

        lower_current = lower_sensor.get_measurement("current")
        lower_power = lower_sensor.get_measurement("power")
        lower_voltage = lower_power / lower_current
        print_lower = "{li:5.3f} A, {lp:6.3f} W, {lv:6.3f} V".format(
            li=lower_current, lp=lower_power, lv=lower_voltage)

        print("{}          {}".format(print_upper, print_lower), end="\r")


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)

    try:
        main()
    except KeyboardInterrupt:
        print()
        sys.exit(0)
