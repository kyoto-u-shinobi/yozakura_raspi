# (C) 2015  Kyoto University Mechatronics Laboratory
# Released under the GNU General Public License, version 3
import ctypes
from collections import OrderedDict
import subprocess

from RPi import GPIO as gpio
import smbus

from common.exceptions import CRCError


i2c_bus = 1  # /dev/i2c-1


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
        self.bus.write_byte(self.write_address, ThermalSensor.start_read)
        self.logger.debug("Reading")
        readout = self.bus.read_i2c_block_data(self.read_address, 35)
        self.logger.debug("Checking error")
        self._error_check(readout)  # Data integrity check

        self.logger.debug("Concatenating data")
        temp_ref = concatenate(readout[:2], endianness="little") / 10
        matrix = [concatenate(readout[i:i+2], endianness="little") / 10
                  for i in range(2, 34, 2)]

        return temp_ref, matrix
    
    @staticmethod
    def _crc8_check(byte):
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

    @staticmethod
    def _error_check(data):
        """Check for data integrity using CRC-8.

        Args:
            data: The buffer to be checked. The error byte has to be the last.

        Raises:
            CRCError: The CRC check failed.
        """
        crc = self._crc8_check(0x15)
        for datum in data:
            crc = self._crc8_check(datum ^ crc)

        if crc != data[-1]:
            raise CRCError("A cyclic redundancy check failed.")


class CurrentSensor(Device):
    """Texas Instruments INA226 Current/Power Monitor.

    All words are big endian.

    References:
        Datasheet: http://www.ti.com/lit/ds/symlink/ina226.pdf

    Attributes:
        address: The address of the device.
        pin_alert: The alert pin of the device. None if not connected.
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

    class ConfigurationBits(ctypes.Structure):
        _fields_ = [("reset", ctypes.c_uint16, 1),
                    ("upper", ctypes.c_uint16, 3),
                    ("avg", ctypes.c_uint16, 3),
                    ("bus_ct", ctypes.c_uint16, 3),
                    ("shunt_ct", ctypes.c_uint16, 3),
                    ("mode", ctypes.c_uint16, 3)]

    class Configuration(ctypes.Union):
        _fields_ = [("bits", CurrentSensor.ConfigurationBits),
                    ("as_byte", ctypes.c_uint16)]

        _anonymous_ = ("bits")

    class AlertsBits(ctypes.Structure):
        _fields_ = [("shunt_ol", ctypes.c_uint16, 1),
                    ("shunt_ul", ctypes.c_uint16, 1),
                    ("bus_ol", ctypes.c_uint16, 1),
                    ("bus_ul", ctypes.c_uint16, 1),
                    ("power_ol", ctypes.c_uint16, 1),
                    ("conv_watch", ctypes.c_uint16, 1),
                    ("empty", ctypes.c_uint16, 5),
                    ("alert_func", ctypes.c_uint16, 1),
                    ("conv_flag", ctypes.c_uint16, 1),
                    ("overflow", ctypes.c_uint16, 1),
                    ("polarity", ctypes.c_uint16, 1),
                    ("latch", ctypes.c_uint16, 1)]

    class Alerts(ctypes.Union):
        _fields_ = [("bits", CurrentSensor.AlertsBits),
                    ("as_byte", ctypes.c_uint16)]

        _anonymous_ = ("bits")

    def __init__(self, address, name="Current Sensor", bus_number=i2c_bus):
        """Inits the current sensor.

        Args:
            address: The address of the device.
            name: (optional) The name of the device.
            bus_number: (optional) The i2c bus being used.
        """
        super().__init__(address, name, bus_number)
        self.pin_alert = None
        self.calibrate(15)

    def _read_register(self, register, complement=True):
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
            if data > 2**16 / 2 - 1:
                return 2**16 - data
        return data

    def _write_register(self, register, data):
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
        config = CurrentSensor.Configuration()
        config.as_byte = self._read_register("config", complement=False)
        return config

    def set_configuration(self, reset=None, avg=None,
                          bus_ct=None, shunt_ct=None, mode=None):
        """Configure the current sensor.

        c.f. page 18 in the datasheet. This function only changes the
        parameters that are specified. All other parameters remain unchanged.

        Args:
            reset: (optional) Whether to reset.
            avg: (optional) The averaging mode.
            bus_ct: (optional) Bus voltage conversion time.
            shunt_ct: (optional) Shunt voltage conversion time.
            mode: (optional) Operating mode.
        """
        self.logger.debug("Setting configuration")
        config = self.get_configuration()

        if reset is not None:
            config.reset = reset
        if avg is not None:
            config.avg = avg
        if bus_ct is not None:
            config.bus_ct = bus_ct
        if shunt_ct is not None:
            config.shunt_ct = shunt_ct
        if mode is not None:
            config.mode = mode

        self._write_register("config", config)

    def reset(self):
        """Reset the current sensor."""
        self.logger.debug("Resetting sensor")
        self.set_configuration(reset=1)

    def get_measurement(self, register):
        """Return the measurement in a register.

        Args:
            register: The name of the register to be read.
        """
        self.logger.debug("Getting {} measurement".format(register))
        # Force a read if triggered mode.
        if 0 < self.get_configuration().mode <= 3:
            self.set_configuration()
        while not self.get_alerts()["ready"]:
            pass

        try:
            return self._read_register(register) * self.lsbs[register]
        except KeyError:
            print("{} is not a measurement.".format(register))
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
        self._write_register("calib", calib_value)

    def set_alerts(self, alert, limit,
                   ready=False, invert=False, latch=False,
                   pin_alert=None, interrupt=False):
        """Set the alerts required.

        The five alert functions are:
            sol: Shunt voltage over limit
            sul: Shunt voltage under limit
            bol: Bus voltage over limit
            bul: Bus voltage under limit
            pol: Power over limit

        Only one may be selected. c.f. page 21 in the datasheet.
        
        The three flags are:
            cnvr: Conversion ready
            apol: Alert polarity
            len: Alert latch enable

        Args:
            alert: A string containing the alert to be triggered.
            limit: The limit at which the alert is triggered, in natural units.
            ready: (optional) Whether to trigger an alert if conversion ready.
                Default is False.
            invert: (optional) Whether to invert the alert pin polarity. Default
                is False.
            latch: (optional) Whether to latch the alert output. Default is
                False.
            pin_alert: (optional) The alert pin, if connected. Default is None.
            interrupt: (optional) Whether to enable interrupts. Default is False.
        """
        self.logger.debug("Setting alerts")
        alerts = CurrentSensor.Alerts()
        functions = {"sol": 15, "sul": 14, "bol": 13, "bul": 12, "pol": 11}
        
        alert_value.as_byte = 1 << functions[alert]
        
        alerts.conv_watch = ready
        alerts.polarity = invert
        alerts.latch = latch

        self._write_register("alert_reg", alerts)

        if alert == "sol" or alert == "sul":
            lsb = self.lsbs["shunt"]
        elif alert == "bol" or alert == "bul":
            lsb = self.lsbs["bus"]
        else:  # alert == "pol"
            lsb = self.lsbs["power"]
        self._write_register("alert_lim", limit/lsb)
        
        if pin_alert is not None:
            self.pin_alert = pin_alert
            gpio.setup(pin_alert, gpio.IN, pull_up_down=gpio.PUD_UP)  # Pull up
            if interrupt:
                gpio.add_event_detect(pin_alert, gpio.FALLING, 
                                      callback=self._catch_alert)

    def _catch_alert(self, channel):
        """Threaded callback for alert detection"""
        self.logger.debug("Alert detected")
        return self.get_alerts()
        
    def get_alerts(self):
        """Check the state of the alerts.

        The three alert flags are:
            aff: Alert function flag
            cvrf: Conversion ready flag
            ovf: Math overflow flag

        Returns:
            A dictionary containing the state of the alerts.
        """
        self.logger.debug("Getting alert flags")
        alerts = CurrentSensor.Alerts()
        alerts.as_byte = self._read_register("alert_reg", complement=False)
        flags = {"aff": alerts.alert_func,
                 "cvrf": alerts.conv_flag,
                 "ovf": alerts.overflow}
        
        # Clear aff bit in the register.
        alerts.alert_func = 0
        self._write_register("alert_reg", alerts)
        
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
    class ConfigurationBits(ctypes.Structure):
        _fields_ = [("ready", ctypes.c_uint8, 1),
                    ("channel", ctypes.c_uint8, 2),
                    ("mode", ctypes.c_uint8, 1),
                    ("rate", ctypes.c_uint8, 2),
                    ("gain", ctypes.c_uint8, 2)]

    class Configuration(ctypes.Union):
        _fields_ = [("bits", ADConverter.ConfigurationBits),
                    ("as_byte", ctypes.c_uint8)]

        _anonymous_ = ("bits")

    def __init__(self, address=0x68, name="ADC", bus_number=i2c_bus):
        """Inits the A/D converter.

        Args:
            address: The address of the device.
            name: (optional) The name of the device.
            bus_number: (optional) The i2c bus being used.
        """
        super().__init__(address, name, bus_number)
        self.mode = 1

    def _read(self):
        """Read a register on the device.

        The first two bytes received contain the data, and the third byte
        contains the configuration.

        Returns:
            The data and the configuration.
            
            The configuration is a dictionary containing:
                ready: Whether or not a conversion is ready.
                channel: The channel selection bits (not used).
                mode: The operating mode.
                rate: The sampling rate; the resolution is tied to this rate.
                gain: The gain of the ADC.
        """
        config = ADConverter.Configuration()
        received = self.bus.read_i2c_byte_data(self.address, 3)
        data = received >> 8
        config.as_byte = received & 0xff
        return data, config

    def get_data(self):
        """Get the converted data from the conversion register.

        Returns:
            The data, converted to natural units.
        """
        # Start reading if in oneshot mode.
        if self.mode:
            self.set_configuration(ready=1)

        data, config = self._read()

        # Loop until we get new data.
        while config.ready:
            data, config = self._read()

        # Set variables.
        n_bits = 12 + 2 * config.rate
        gain = 2**config.gain

        lsb = 2 * 2.048 / (2 ** n_bits)
        max_code = 2 ** (n_bits - 1) - 1

        # Only use n_bits bits.
        data &= ~(0b1111 << n_bits)

        # Get two's complement if negative.
        if data > 2**n_bits / 2 - 1:
            data = 2**n_bits - data
            sign = -1
        else:
            sign = 1

        # Calculate result
        result = data / (max_code + 1) / gain * 2.048

        return result * sign

    def get_configuration(self):
        """Read the ADC configuration.

        Returns:
            The configuration.
        """
        data, config = self._read()
        return config

    def set_configuration(self, ready=None, mode=None, rate=None, gain=None):
        """Configure the A/D converter.

        This function only changes the parameters that are specified. All other
        parameters remain unchanged.

        Args:
            ready: (optional) The conversion ready bit. Set to 1 after reading
                in continuous oneshot mode.
            mode: (optional) The conversion mode. Continuous (1) or oneshot (0).
            rate: (optional) The sample rate. Can be 0~2.
            gain: (optional) The PGA gain. Can be 0~3.
        """
        self.logger.debug("Configuring ADC")
        config = self.get_configuration()

        if ready is not None:
            config.ready = ready
        if mode is not None:
            config.mode = mode
        if rate is not None:
            config.rate = rate
        if gain is not None:
            config.gain = gain

        self.bus.write_byte(self.address, config)


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
