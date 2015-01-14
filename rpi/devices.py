# (C) 2015  Kyoto University Mechatronics Laboratory
# Released under the GNU General Public License, version 3
from collections import OrderedDict
import subprocess

import smbus


i2c_bus = 1  # /dev/i2c-1


class CRCError(ValueError):
    """This exception is raised when a cyclic redundancy check fails."""
    pass


def get_used_i2c_slots(bus_number=i2c_bus):
    """Find all used i2c slots.

    Args:
        bus: (optional) The bus to be used.

    Returns:
        A dictionary containing all used i2c slots and their values.
    """
    slots = OrderedDict()
    command = "i2cdetect -y {}".format(bus_number)
    table = subprocess.check_output(command.split()).splitlines()[1:]
    for i, row in enumerate(table):
        row = str(row, encoding="utf-8")
        for j, item in enumerate(row.split()[1:]):
            if item != "--":
                slots[16*i + (j if i > 0 else j + 3)] = item
    return slots


def concatenate(byte_array, endianness="big", size=8):
    """Concatenates multiple bytes to form a single number.

    Args:
        byte_array: The array of bytes to be concatenated.
        endianness: (optional) Can be big endian or little endian. Default is
            big endian.
        size: Number of bits per byte.

    Returns:
        The result of the concatenation.

    Raises:
        ValueError: A bad argument was given.
    """
    total = 0
    if endianness=="big":
        for byte in byte_array:
            total = (total << size) + byte

    elif endianness=="little":
        for byte in reversed(byte_array):
            total = (total << size) + byte

    else:
        raise ValueError("{} is not a valid argument for endianness. \
                          Please try either \"big\" or \"little\"".format(endianness))
    return total


class Device(object):
    """This is a catch-all for i2c devices.

    Attributes:
        address: The address of the i2c device
        name: The name of the device.
        bus_number: The i2c bus being used.
        devices: A class variable containing all registered devices.
    """
    devices = {}

    def __init__(self, address, name, bus_number=i2c_bus):
        """Inits and registers the device.

        Args:
            address: The address of the i2c device
            name: The name of the device.
            bus_number: (optional) The i2c bus being used.

        Raises:
            KeyError: The address is valid, but another device has already been
                registered at that address and has not been removed yet.
        """
        self.logger = logging.getLogger("i2c-{}-{}".format(name, hex(address)))
        self.logger.debug("Initializing device")
        slots = get_used_i2c_slots()
        if address not in slots.keys():
            self.logger.warning("No device detected")
        elif slots[address] == "UU":
            self.logger.warning("Device at address is busy")
        elif address in Device.devices.values():
            raise KeyError("A device is already registered at this address.")
        else:
            self.address = address
            self.name = name
            self.bus = smbus.SMBus(bus_number)
            Device.devices[self] = address
        self.logger.info("Device initialized")

    def remove(self):
        """Deregister the device."""
        self.logger.info("Deregistering device")
        del Device.devices[self]

    def __repr__(self):
        return "{} at {} ({})".format(self.__class__.__name__,
                                      hex(self.address), self.name)

    def __str__(self):
        return self.name


class ThermalSensor(Device):
    """Omron D6T-44L-06 Thermal Sensor.

    The device returns a 4x4 matrix containing temperatures. It has two
    addresses: a write address and a read address. It needs a write before
    starting to read.

    References:
        Application note: http://goo.gl/KzvjIv

    Attributes:
        write_address: The write address of the device.
        read_address: The read address of the device.
        address: A tuple containing the write and read addresses.
        name: The name of the device.
        bus_number: The i2c bus being used.
    """
    start_read = 0x4C

    def __init__(self, write_address=0x14, read_address=0x15,
                 name="Thermal Sensor", bus_number=i2c_bus):
        """Inits the thermal sensor.

        Args:
            write_address: The write address of the device.
            read_address: The read address of the device.
            name: (optional) The name of the device.
            bus_number: (optional) The i2c bus being used.
        """
        super().__init__((write_address, read_address), name, bus_number)
        self.write_address = write_address
        self.read_address = read_address

    def get_temperature_matrix(self):
        """Return the temperature matrix.

        0x4C is first written to the write address, then 35 bytes are read.
        Error detection is provided using CRC-8. All words are little-endian.
        Temperature data consists of 16-bit signed ints, 10x Celcius value.

        The structure of the readout is:
            2 bytes: Reference temperature.
            32 bytes: Cell temperature for 16 cells.
            1 byte: Error bit.

        Returns:
            temp_ref: The reference temperature
            matrix: The temperature matrix.

        Raises:
            CRCError: A CRC check failed. i.e., bad data was received.
        """
        self.logger.debug("Getting temperature")
        self.logger.debug("Writing to start read")
        self.bus.write_byte_data(self.write_address, ThermalSensor.start_read)
        self.logger.debug("Reading")
        readout = self.bus.read_i2c_block_data(self.read_address, 0, 35)
        self.logger.debug("Checking error")
        self._error_check(readout)  # Data integrity check

        self.logger.debug("Concatenating data")
        temp_ref = concatenate(readout[:2], endianness="little") / 10
        matrix = [concatenate(readout[i:i+2], endianness="little") / 10
                  for i in range(2, 34, 2)]

        return temp_ref, matrix

    @staticmethod
    def _error_check(data):
        """Check for data integrity using CRC-8.

        Args:
            data: The buffer to be checked. The error byte has to be the last.

        Raises:
            CRCError: The CRC check failed.
        """
        def crc8_check(byte):
            """Perform a cyclic redundancy check calculation for CRC-8.

            Args:
                byte: The byte to perform the calculation on.

            Returns:
                The result of the calculation.
            """
            for i in range(8):
                temp = byte
                byte <<= 1
                if temp & 0x80:
                    byte ^= 0x07
            return byte

        crc = crc8_check(0x15)
        for datum in data:
            crc = crc8_check(datum ^ crc)

        if crc != data[-1]:
            raise CRCError("A cyclic redundancy check failed.")


class CurrentSensor(Device):
    """Texas Instruments INA226 Current/Power Monitor.

    All words are big endian.

    References:
        Datasheet: http://www.ti.com/lit/ds/symlink/ina226.pdf

    Attributes:
        address: The address of the device.
        name: The name of the device.
        bus_number: The i2c bus being used.
        registers: A dictionary containing the addresses of each register.
        lsbs: The value of the least significant bit of each register.
    """
    registers = {"config": 0,
                 "v_shunt": 1,
                 "v_bus": 2,
                 "power": 3,
                 "current": 4,
                 "calib": 5,
                 "alert_reg": 6,
                 "alert_lim": 7,
                 "die": 0xFF}

    lsbs = {"v_shunt": 2.5e-6,  # Volts
            "v_bus": 1.25e-3,  # Volts
            "power": None,  # Watts
            "current": None}  # Amperes

    def __init__(self, address, name="Current Sensor", bus_number=i2c_bus):
        """Inits the current sensor.

        Args:
            address: The address of the device.
            name: (optional) The name of the device.
            bus_number: (optional) The i2c bus being used.
        """
        super().__init__(address, name, bus_number)
        self.calibrate(15)

    def read_register(self, register, complement=True):
        """Read a register on the device.

        Args:
            register: The name of the register to be read.
            complement: (optional) Whether the result is a signed integer.
                Default is true.

        Returns:
            The data from the register. If the result is a signed integer,
            return its two's complement.
        """
        self.logger.debug("Reading {} register".format(register))
        data = self.bus.read_word_data(self.address, self.registers[register])
        data = ((data & 0xff) << 8) + (data >> 8)  # Switch byte order

        if complement:
            if data > 2**16/2-1:
                return 2**16 - data
        return data

    def write_register(self, register, data):
        """Write to a register on the device.

        Args:
            register: The name of the register to be written to.
            data: The data to be written.
        """
        self.logger.debug("Writing {} to {} register".format(data, register))
        data = int(data)
        data = ((data & 0xff) << 8) + (data >> 8)  # Switch byte order
        self.bus.write_word_data(self.address, self.registers[register], data)

    def get_configuration(self):
        """Read the current sensor configuration.

        Returns:
            A dictionary containing:
                upper: The upper four bits (not used).
                avg: The averaging mode.
                bus_ct: Bus voltage conversion time.
                shunt_ct: Shunt voltage conversion time.
                mode: Operating mode.
        """
        self.logger.debug("Getting configuration")
        read_result = self.read_register("config", complement=False)
        config = OrderedDict()
        config["upper"] = (read_result & (0b1111<<12)) >> 12
        config["avg"] = (read_result & (0b111<<9)) >> 9
        config["bus_ct"] = (read_result & (0b111<<6)) >> 6
        config["shunt_ct"] = (read_result & (0b111<<3)) >> 3
        config["mode"] = read_result & (0b111)
        return config

    def configure(self, avg=None, bus_ct=None, shunt_ct=None, mode=None):
        """Configures the current sensor.

        c.f. page 18 in the datasheet. This function only changes the
        parameters that are specified. All other parameters remain unchanged.

        Args:
            avg: (optional) The averaging mode.
            bus_ct: (optional) Bus voltage conversion time.
            shunt_ct: (optional) Shunt voltage conversion time.
            mode: (optional) Operating mode.
        """
        self.logger.debug("Setting configuration")
        config = self.get_configuration()
        upper = config["upper"] << 12
        if avg is None:
            avg = config["avg"] << 9
        else:
            avg = avg<<9
        if bus_ct is None:
            bus_ct = config["bus_ct"] << 6
        else:
            bus_ct = bus_ct<<6
        if shunt_ct is None:
            shunt_ct = config["shunt_ct"] << 3
        else:
            shunt_ct = shunt_ct<<3
        if mode is None:
            mode = config["mode"]

        self.write_register("config", upper + avg + bus_ct + shunt_ct + mode)

    def reset(self):
        """Reset the current sensor."""
        self.logger.debug("Resetting sensor")
        self.write_register("config", 0b1<<15)

    def get_measurement(self, register):
        """Return the measurement in a register.

        Args:
            register: The name of the register to be read.
        """
        self.logger.debug("Getting {} measurement".format(register))
        # Force a read if triggered mode.
        if 0 < self.get_configuration()["mode"] <= 3:
            self.configure()
        while not self.get_alerts()["ready"]:
            pass

        try:
            return self.read_register(register) * self.lsbs[register]
        except KeyError:
            print("{} is not a measurement. Try the read_register() function \
                   if you want to read any known register.".format(register))
            raise
        except TypeError:
            print("{} has not been calibrated yet!".format(self))
            raise

    def calibrate(self, max_current, r_shunt=0.002):
        """Calibrate the current sensor.

        The minimum usable max_current is 2.6 A, with a resolution of 0.08 mA.

        Args:
            max_current: The maximum current expected, in Amperes.
            r_shunt: (optional) The resistance of the shunt resistor, in Ohms.
                The resistor used on the sensor is 0.002 Ohms.

        Raises:
            ValueError: The max_current value is too small.
        """
        self.logger.debug("Calibrating sensor")
        if max_current < 2.6:
            raise ValueError("max_current should be at least 2.6 A.")
        self.lsbs["current"] = max_current / 2**15  # Amperes
        self.lsbs["power"] = 25 * self.lsbs["current"]  # Watts
        calib_value = 0.00512 / (self.lsbs["current"] * r_shunt)
        self.write_register("calib", calib_value)

    def set_alerts(self, alert, limit, ready=False, invert=False, latch=False):
        """Set the alerts required.

        The five alert functions are:
            sol: Shunt voltage over limit
            sul: Shunt voltage under limit
            bol: Bus voltage over limit
            bul: Bus voltage under limit
            pol: Power over limit

        Only one may be selected. c.f. page 21 in the datasheet.

        Args:
            alert: A string containing the alert to be triggered.
            limit: The limit at which the alert is triggered, in natural units.
            ready: (optional) Whether to trigger an alert if conversion ready.
            invert: (optional) Whether to invert the alert pin polarity.
            latch: (optional) Whether to latch the alert output.
        """
        self.logger.debug("Setting alerts")
        alerts = {"sol": 15, "sul": 14, "bol": 13, "bul": 12, "pol": 11,
                  "cnvr": 10, "apol": 1, "len": 0}
        alert_value = 1<<alerts[alert]
        if ready:
            alert_value += 1<<alerts["cnvr"]
        if invert:
            alert_value += 1<<alerts["apol"]
        if latch:
            alert_value += 1<<alerts["len"]
        self.write_register("alert_reg", alert_value)

        if alert == "sol" or alert == "sul":
            lsb = self.lsbs["shunt"]
        elif alert == "bol" or alert == "bul":
            lsb = self.lsbs["bus"]
        else:  # alert == "pol"
            lsb = self.lsbs["power"]
        self.write_register("alert_lim", limit/lsb)

    def get_alerts(self):
        """Check the state of the alerts.

        Returns:
            A dictionary containing the state of the alerts.
        """
        self.logger.debug("Getting alert flags")
        data = self.read_register("alert_reg", complement=False)
        alerts = {"aff": 4, "cvrf": 3, "ovf": 2}
        flags = {"alert": (data & (1<<alerts["aff"]) > 0),
                 "ready": (data & (1<<alerts["cvrf"]) > 0),
                 "overflow": (data & (1<<alerts["ovf"]) > 0)}
        return flags


class ADConverter(Device):
    """Microchip MCP3425 16-bit Analog-to-Digital Converter.

    All words are big endian.

    References:
        Datasheet: http://ww1.microchip.com/downloads/en/DeviceDoc/22072b.pdf

    Attributes:
        address: The address of the device.
        name: The name of the device.
        bus_number: The i2c bus being used.
    """
    def __init__(self, address, name="ADC", bus_number=i2c_bus):
        """Inits the A/D converter.

        Args:
            address: The address of the device.
            name: (optional) The name of the device.
            bus_number: (optional) The i2c bus being used.
        """
        super().__init__(address, name, bus_number)

    def configure(self, mode=None, sample_rate=None, gain=None):
        """Configure the A/D converter.

        This function only changes the parameters that are specified. All other
        parameters remain unchanged.

        Args:
            mode: (optional) The conversion mode. Continuous (1) or
                One-shot (0).
            sample_rate: (optional) The sampling rate. Can be 0~2.
            gain: (optional) The PGA gain. Can be 0~3.
        """
        self.logger.debug("Configuring ADC")
        config = self.bus.read_byte(self.address)
        upper = config & (0b111<<5)
        if mode is None:
            mode = config & (1<<4)
        else:
            mode = mode<<4
        if sample_rate is None:
            sample_rate = config & (0b11<<2)
        else:
            sample_rate = sample_rate<<2
        if gain is None:
            gain = config & (0b11)

        configuration = upper + mode + sample_rate + gain
        self.bus.write_byte(self.address, configuration)


def __test_current_sensor():
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
        lower_current = lower_sensor.get_measurement("current")
        lower_power = lower_sensor.get_measurement("power")
        lower_voltage = lower_power / lower_current
        print_upper = "{:5.3f} A, {:6.3f} W, {:6.3f} V".format(upper_current,
                                                               upper_power,
                                                               upper_voltage)
        print_lower = "{:5.3f} A, {:6.3f} W, {:6.3f} V".format(upper_current,
                                                               upper_power,
                                                               upper_voltage)
        print("{}          {}".format(print_upper, print_lower), end="\r")


if __name__ == "__main__":
    __test_current_sensor()
