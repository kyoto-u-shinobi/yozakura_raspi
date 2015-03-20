# (C) 2015  Kyoto University Mechatronics Laboratory
# Released under the GNU General Public License, version 3
"""
Functions and classes for using I2C devices.

Provides functions to simplify work with I2C devices, as well as classes for
each attached device.

"""
from collections import OrderedDict
import logging
import subprocess

from RPi import GPIO as gpio
import smbus

from common.exceptions import InvalidArgError, I2CSlotBusyError, \
    NotCalibratedError
from rpi.bitfields import CurrentConfiguration, CurrentAlerts, ADCConfiguration


i2c_bus = 1  # /dev/i2c-1


def get_used_i2c_slots(bus_number=i2c_bus):
    """
    Find all used i2c slots.

    This function calls an external ``i2cdetect`` command, and works on the
    resultant table to find out which slots are occupied.

    Parameters
    ----------
    bus : int, optional
        The bus to be used.

    Returns
    -------
    slots : dict
        Contains all used i2c slots and their values.

        **Dictionary format :** {slot_number (int): slot_number_hex (str)}

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


def require_repeated_start():
    """
    Enable repeated start conditions for I2C register reads.
    
    This is the normal behaviour for I2C. However, on the Raspberry Pi,
    there is a bug which disables repeated starts unless explicitly enabled
    with this function.
    
    The bug occurs during register reads, and does not send a repeated start
    condition as the Linux kernel smbus I2C driver functions define. As a
    workaround, this bit in the BMC2708 driver sysfs tree can be changed to
    enable I2C repeated starts.
    
    Note that the Raspberry Pi models A, B, and B+ all use the BMC2835 CPU,
    and the Raspberry Pi 2 uses the BCM2836 CPU. [1]_ Both CPUs are
    implementations of the BCM2708 series, [2]_ so this fix should work for
    all models.
    
    See this Raspberry Pi forum thread for more details. [3]_
    
    This function is based on an Adafruit I2C implementation, shown to
    @masasin by Tony DiCola, one of the authors and contributors. [4]_
    
    References
    ----------
    .. [1] Wikipedia. "Raspberry Pi."
           https://en.wikipedia.org/wiki/Raspberry_Pi
           
    .. [2] Linux, Raspberry Pi, Github. "Issue #22. BCM2708 vs. BCM2835."
           https://github.com/raspberrypi/linux/issues/22
           
    .. [3] Raspberry Pi Forums. "i2c repeated start transactions"
           http://www.raspberrypi.org/forums/viewtropic.php?f=44&t=15840
    
    .. [4] Adafruit Python GPIO, Adafruit, Github. "I2C.py"
           https://github.com/adafruit/Adafruit_Python_GPIO/blob/master/Adafruit_GPIO/I2C.py#L68
    
    """
    sysfs_tree = "/sys/module/i2c_bcm2708/parameters/combined"
    subprocess.check_call("chmod 666 {}".format(sysfs_tree), shell=True)
    subprocess.check_call("echo -n 1 > {}".format(sysfs_tree), shell=True)


def concatenate(byte_array, big_endian=True, size=8):
    """
    Concatenate multiple bytes to form a single number.

    Parameters
    ----------
    byte_array : byte_array
        The array of bytes to be concatenated.
    big_endian : bool, optional
        Whether the byte array is big endian.
    size : int, optional
        Number of bits per byte.

    Returns
    -------
    total : int
        The result of the concatenation.

    Raises
    ------
    InvalidArgError
        A bad argument was given.

    """
    total = 0
    for byte in (byte_array if big_endian else reversed(byte_array)):
        total = (total << size) + byte
    return total


class Device(object):
    """
    Parent class for all I2C devices. Provides registration and deregistration.

    Parameters
    ----------
    address : byte
        The address of the i2c device.
    name : str
        The name of the device.
    bus_number : int, optional
        The I2C bus being used.

    Raises
    ------
    I2CSlotBusyError
        The address is valid, but another device has already been registered at
        that address and has not been removed yet.

    Attributes
    ----------
    address : byte
        The address of the I2C device.
    name : str
        The name of the device.
    bus_number : int
        The I2C bus being used.
    devices : dict
        Contains all registered devices.

        Dictionary format: {address (str): device (Device)}

    """
    devices = {}
    # TODO(masasin): Fix segfaulting.
    # require_repeated_start()

    def __init__(self, address, name, bus_number=i2c_bus):
        self.logger = logging.getLogger("i2c-{}-{}".format(name, hex(address)))
        self.logger.debug("Initializing device")
        slots = get_used_i2c_slots()
        if address not in slots.keys():
            self.logger.warning("No device detected")
        elif slots[address] == "UU":
            self.logger.warning("Device at address is busy")
        elif address in Device.devices.values():
            self.logger.error("Address belongs to a registered device.")
            raise I2CSlotBusyError
        else:
            self.address = address
            self.name = name
            self.bus = smbus.SMBus(bus_number)
            Device.devices[address] = self
        self.logger.info("Device initialized")

    def remove(self):
        """Deregister the device."""
        self.logger.info("Deregistering device")
        del Device.devices[self.address]

    def __repr__(self):
        return "{} at {} ({})".format(self.__class__.__name__,
                                      hex(self.address), self.name)

    def __str__(self):
        return self.name


class ThermalSensor(Device):
    """
    Omron D6T-44L-06 Thermal Sensor. [1]_

    The device returns a 4x4 matrix containing temperatures. It has two
    addresses: a write address and a read address. The ``start_read`` byte
    needs to be written to the address before starting to read. [2]_

    .. note:: All words are little-endian.

    Parameters
    ----------
    address : byte, optional
        The address of the device.
    name : str, optional
        The name of the device.
    bus_number : int, optional
        The I2C bus being used.

    Attributes
    ----------
    address : byte
        The address of the device.
    name : str
        The name of the device.
    bus_number : int
        The I2C bus being used.
    start_read : byte
        The byte to be written to start a read.

    References
    ----------
    .. [1] Omron, D6T-44L-06 datasheet.
           http://www.omron.com/ecb/products/pdf/en-d6t.pdf

    .. [2] Omron, D6T-44L-06 application note 01.
           http://www.omron.com/ecb/products/sensor/special/mems/pdf/AN-D6T-01EN_r2.pdf

    """
    start_read = 0x4C  # Defined in the application note.

    def __init__(self, address=0xa, name="Thermal Sensor", bus_number=i2c_bus):
        super().__init__(address, name, bus_number)

    def get_temperature_matrix(self):
        """
        Return the temperature matrix.

        0x4C is first written to the device, then 35 bytes are read.

        Error detection is provided using CRC-8. Temperature data consists of
        16-bit signed ints, 10x Celsius value.

        The structure of the readout is:
            - 2 bytes : Reference temperature.
            - 32 bytes : Cell temperature for 16 cells.
            - 1 byte : Error byte.
        
        This function is based on an official application note. [1]_

        Returns
        -------
        temp_ref : float
            The reference temperature, in Celsius.
        matrix : list of float
            The temperature matrix, containing 16 temperatures in Celsius.
        good_data : bool
            Whether the data is good.
        
        
        References
        ----------
        .. [1] Omron, D6T-44L-06 application note 01.
               http://www.omron.com/ecb/products/sensor/special/mems/pdf/AN-D6T-01EN_r2.pdf

        """
        self.logger.debug("Getting temperature")
        readout = self.bus.read_i2c_block_data(self.address,
                                               ThermalSensor.start_read,
                                               35)
                                               
        self.logger.debug("Checking error")
        good_data = self._error_check(readout)  # Data integrity check
        if not good_data:
            self.logger.warning("CRC check fialed.")

        self.logger.debug("Concatenating data")
        temp_ref = concatenate(readout[:2], big_endian=False) / 10
        matrix = [concatenate(readout[i:i+2], big_endian=False) / 10
                  for i in range(2, 34, 2)]

        return temp_ref, matrix, good_data

    @staticmethod
    def _crc8_check(data):
        """
        Perform a cyclic redundancy check calculation for CRC-8.

        Args
        ----
        data : byte
            The byte to perform the calculation on.

        Returns
        -------
        data : byte
            The result of the calculation.

        """
        for i in range(8):
            temp = data
            data <<= 1
        if temp & 0x80:
            data ^= 0x07
        return data

    def _error_check(self, data):
        """
        Check for data integrity using CRC-8.

        Parameters
        ----------
        data : byte_array
            The buffer to be checked. Must have the error byte as the last
            byte.

        Returns
        -------
        bool
            Whether the data is good.

        """
        crc = self._crc8_check(0x15)
        for datum in data[:-1]:
            crc = self._crc8_check(datum ^ crc)

        return crc == data[-1]


class CurrentSensor(Device):
    """
    Texas Instruments INA226 Current/Power Monitor. [1]_

    The current sensor must be calibrated before use.

    .. note:: All words are big endian.

    Parameters
    ----------
    address : byte
        The address of the device.
    name : str, optional
        The name of the device.
    bus_number : int, optional
        The I2C bus being used.

    Attributes
    ----------
    address : byte
        The address of the device.
    pin_alert : int
        The alert pin of the device. None if not connected.
    name : str
        The name of the device.
    bus_number : int
        The I2C bus being used.
    registers : dict
        Contains the addresses of each register.

        **Dictionary format :** {register (str): address (int)}

        config : str
            Configuration register
        v_shunt : str
            Shunt voltage measurement register
        v_bus : str
            Bus voltage measurement register
        power : str
            Power measurement register
        current : str
            Current measurement register
        calib : str
            Calibration register
        alert_reg : str
            Mask/Enable register
        alert_lim : str
            Alert limit register
        die : str
            Die ID
    lsbs : dict
        Contains the value of the least significant bit of each measurement
        register.

        **Dictionary format :** {register (str): lsb (float)}

        v_shunt : str
            Shunt voltage result register
        v_bus : str
            Bus voltage result register
        power : str
            Power result register
        current : str
            Current result register

    References
    ----------
    .. [1] Texas Instruments, INA 226 datasheet.
           http://www.ti.com/lit/ds/symlink/ina226.pdf

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

    def __init__(self, address, name="Current Sensor", bus_number=i2c_bus):
        self.lsbs = {"v_shunt": 2.5e-6,  # Volts
                     "v_bus": 1.25e-3,  # Volts
                     "power": None,  # Watts
                     "current": None}  # Amperes

        super().__init__(address, name, bus_number)
        self.pin_alert = None
        self.calibrate(15)  # 15 A max current.

    def _read_register(self, register, signed=True):
        """
        Read a register on the device.

        Parameters
        ----------
        register : str
            The name of the register to be read.
        signed : bool, optional
            Whether the result is a signed integer.

        Returns
        -------
        data : word
            The data from the register. If the result is a signed integer,
            return its two's complement.

        """
        self.logger.debug("Reading {} register".format(register))
        data = self.bus.read_word_data(self.address, self.registers[register])
        data = ((data & 0xff) << 8) + (data >> 8)  # Switch byte order

        if signed:
            if data > 2**15 - 1:
                return data - 2**16
        return data

    def _write_register(self, register, data):
        """
        Write to a register on the device.

        Parameters
        ----------
        register : str
            The name of the register to be written to.
        data : word
            The data to be written.
        """
        self.logger.debug("Writing {} to {} register".format(data, register))
        data = int(data)

        # bus.write_word_data writes one byte at a time, so we switch the byte
        # order before writing.
        data = ((data & 0xff) << 8) + (data >> 8)  # Switch byte order
        self.bus.write_word_data(self.address, self.registers[register], data)

    def get_configuration(self):
        """
        Read the current sensor configuration.

        See pages 18 and 19 in the datasheet [1]_ for more information.

        Returns
        -------
        config : CurrentConfiguration
            The configuration word. Bit fields:

            reset : bool
                Whether to reset.
            empty : 3 bits
                Not used.
            avg : 3 bits
                Averaging mode. Can range between 0 and 7.
            bus_ct : 3 bits
                Bus voltage conversion time. Can range between 0 and 7.
            shunt_ct : 3 bits
                Shunt voltage conversion time. Can range between 0 and 7.
            mode : 3 bits
                Operating mode. Can range between 0 and 7.

        See Also
        --------
        CurrentConfiguration

        References
        ----------
        .. [1] Texas Instruments, INA 226 datasheet.
               http://www.ti.com/lit/ds/symlink/ina226.pdf

        """
        self.logger.debug("Getting configuration")
        config = CurrentConfiguration()
        config.as_byte = self._read_register("config", signed=False)
        return config

    def set_configuration(self, reset=None, avg=None,
                          bus_ct=None, shunt_ct=None, mode=None):
        """
        Configure the current sensor.

        See pages 18 and 19 in the datasheet. [1]_ This function only changes
        the parameters that are specified. All other parameters remain
        unchanged.

        Parameters
        ----------
        reset : bool, optional
            Whether to reset. This overrides all other data. Use via the
            ``reset`` method.
        avg : int, optional
            The averaging mode. Can range between 0 and 7.
        bus_ct : int, optional
            Bus voltage conversion time. Can range between 0 and 7.
        shunt_ct : int, optional
            Shunt voltage conversion time. Can range between 0 and 7.
        mode : int, optional
            Operating mode. Can range between 0 and 7.

        References
        ----------
        .. [1] Texas Instruments, INA 226 datasheet.
               http://www.ti.com/lit/ds/symlink/ina226.pdf

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
        """
        Get the measurement in a register.

        Parameters
        ----------
        register : str
            The name of the register to be read.

        Returns
        -------
        float
            The value of the measurement, in natural units.

        Raises
        ------
        InvalidArgError
            The register specified does not contain a measurement.
        NotCalibratedError
            The device has not yet been calibrated.

        """
        self.logger.debug("Getting {} measurement".format(register))
        # Force a read if triggered mode.
        if 0 < self.get_configuration().mode <= 3:
            self.set_configuration()
        while not self.get_alerts()["ready"]:
            pass

        if register not in self.lsbs:
            self.logger.error("{} is not a measurement!".format(register))
            raise InvalidArgError("{} is not a measurement!".format(register))
        try:
            return self._read_register(register) * self.lsbs[register]
        except TypeError:
            self.logger.error("{} has not been calibrated yet!".format(self))
            raise NotCalibratedError(self)

    def calibrate(self, max_current, r_shunt=0.002):
        """
        Calibrate the current sensor.

        The device must be calibrated before use. Calibration sets the
        calibration register, and determines the LSB values for the current
        and power measurement registers.

        The minimum usable max_current is 2.6 A, with a resolution of 0.08 mA.

        Parameters
        ----------
        max_current : float
            The maximum current expected, in Amperes.
        r_shunt : float, optional
            The resistance of the shunt resistor, in Ohms. The resistor used on
            the sensor board is 0.002 Ohms.

        Raises
        ------
        InvalidArgError
            The max_current value is too small.

        """
        self.logger.debug("Calibrating sensor")
        if max_current < 2.6:
            raise InvalidArgError("max_current should be at least 2.6 A.")

        self.lsbs["current"] = max_current / 2**15  # Amperes
        self.lsbs["power"] = 25 * self.lsbs["current"]  # Watts
        calib_value = 0.00512 / (self.lsbs["current"] * r_shunt)
        self._write_register("calib", calib_value)

    def set_alerts(self, alert, limit,
                   ready=False, invert=False, latch=False,
                   pin_alert=None, interrupt=False):
        """
        Choose the alert function and set up the alert behaviour.

        See pages 21 and 22 of the datasheet [1]_ for more information.

        Only one alert function may be selected. The five possible alert
        functions are:
            sol : str
                Shunt voltage over limit.
            sul : str
                Shunt voltage under limit.
            bol : str
                Bus voltage over limit.
            bul : str
                Bus voltage under limit.
            pol : str
                Power over limit.

        In addition, three bits can be used to set the Mask/Enable register's
        behaviour. The three flags are:
            cnvr : bool
                Conversion ready
            apol : bool
                Invert alert polarity
            len : bool
                Alert latch enable

        Parameters
        ----------
        alert : str
            The alert function to be enabled.
        limit : float
            The limit at which the alert is triggered, in natural units.
        ready : bool, optional
            Whether to trigger an alert if conversion ready.
        invert : bool, optional
            Whether to invert the alert pin polarity.
        latch : bool, optional
            Whether to latch the alert output.
        pin_alert : int, optional
            The alert pin, if connected.
        interrupt : bool, optional
            Whether to enable interrupts.

        References
        ----------
        .. [1] Texas Instruments, INA 226 datasheet.
               http://www.ti.com/lit/ds/symlink/ina226.pdf

        """
        self.logger.debug("Setting alerts")
        alerts = CurrentAlerts()
        functions = {"sol": 15, "sul": 14, "bol": 13, "bul": 12, "pol": 11}

        alerts.as_byte = 1 << functions[alert]

        alerts.conv_watch = ready
        alerts.invert = invert
        alerts.latch = latch

        self._write_register("alert_reg", alerts)

        if alert == "sol" or alert == "sul":
            lsb = self.lsbs["shunt"]
        elif alert == "bol" or alert == "bul":
            lsb = self.lsbs["bus"]
        else:  # alert == "pol"
            lsb = self.lsbs["power"]
        self._write_register("alert_lim", limit / lsb)

        if pin_alert is not None:
            self.pin_alert = pin_alert
            gpio.setup(pin_alert, gpio.IN,
                       pull_up_down=gpio.PUD_UP if invert else gpio.PUD_DOWN)
            if interrupt:
                gpio.add_event_detect(pin_alert,
                                      gpio.FALLING if invert else gpio.RISING,
                                      callback=self._catch_alert)

    def _catch_alert(self, channel):
        """Threaded callback for alert detection"""
        self.logger.debug("Alert detected")

    def get_alerts(self):
        """
        Check the state of the alerts.

        Returns:
        flags : dict
            Contains the state of the alerts. Dictionary fields:

            aff : str
                Alert function flag
            cvrf : str
                Conversion ready flag
            ovf : str
                Math overflow flag

        """
        self.logger.debug("Getting alert flags")
        alerts = CurrentAlerts()
        alerts.as_byte = self._read_register("alert_reg", signed=False)
        flags = {"aff": alerts.alert_func,
                 "cvrf": alerts.conv_flag,
                 "ovf": alerts.overflow}

        # Clear aff bit in the register.
        alerts.alert_func = 0
        self._write_register("alert_reg", alerts)

        return flags


def __test_current_sensor():
    """
    Test the current sensor.

    This assumes that there are two current sensors. One is connected to the
    high voltage side, and has an address of 0x40. The other is connected to
    the low voltage side, and has an address of 0x44. Both current sensors
    should show the same values for current and power and voltage.

    """
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


def __test_thermal_sensor():
    """
    Test the thermal sensor.
    
    This assumes that the thermal sensor is connected properly.
    
    """
    thermal_sensor = ThermalSensor()
    while True:
        temp_ref, matrix, good_data = thermal_sensor.get_temperature_matrix()
        if not good_data:
            print("CRC Error!")
        print(temp_ref)
        for i in range(4):
            for j in range(4):
                print(matrix[i * 4 + j], end=" ")
            print()


if __name__ == "__main__":
    __test_current_sensor()
