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
import RTIMU
import smbus

from common.exceptions import BadArgError, I2CSlotBusyError, \
    NotCalibratedError
from rpi.bitfields import CurrentConfiguration, CurrentAlerts


i2c_bus = 1


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

    def __init__(self, address, name, bus_number=i2c_bus):
        self._logger = logging.getLogger("i2c-{name}-{address}".format(
                                         name=name,
                                         address=hex(address)))
        self._logger.debug("Initializing device")
        slots = get_used_i2c_slots()
        if address not in slots.keys():
            self._logger.warning("No device detected")
        elif slots[address] == "UU":
            self._logger.warning("Device at address is busy")
        elif address in Device.devices.values():
            self._logger.error("Address belongs to a registered device.")
            raise I2CSlotBusyError
        else:
            self.address = address
            self.name = name
            self.bus = smbus.SMBus(bus_number)
            Device.devices[address] = self
        self._logger.info("Device initialized")

    def remove(self):
        """Deregister the device."""
        self._logger.info("Deregistering device")
        del Device.devices[self.address]

    def __repr__(self):
        return "{} at {} ({})".format(self.__class__.__name__,
                                      hex(self.address), self.name)

    def __str__(self):
        return self.name


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
        self.calibrate(10)  # 10 A max current.

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
        self._logger.debug("Reading {} register".format(register))
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
        self._logger.debug("Writing {} to {} register".format(data, register))
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
        self._logger.debug("Getting configuration")
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
        self._logger.debug("Setting configuration")
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

        self._write_register("config", config.as_byte)

    def reset(self):
        """Reset the current sensor."""
        self._logger.debug("Resetting sensor")
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
        BadArgError
            The register specified does not contain a measurement.
        NotCalibratedError
            The device has not yet been calibrated.

        """
        self._logger.debug("Getting {} measurement".format(register))
        # Force a read if triggered mode.
        if 0 < self.get_configuration().mode <= 3:
            self.set_configuration()
        #if self.pin_alert is not None:
            #while not self.get_alerts()["cvrf"]:
                #pass

        if register not in self.lsbs:
            self._logger.error("{} is not a measurement!".format(register))
            raise BadArgError("{} is not a measurement!".format(register))
        try:
            return self._read_register(register) * self.lsbs[register]
        except TypeError:
            self._logger.error("{} has not been calibrated yet!".format(self))
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
        BadArgError
            The max_current value is too small.

        """
        self._logger.debug("Calibrating sensor")
        if max_current < 2.6:
            raise BadArgError("max_current should be at least 2.6 A.")

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
        self._logger.debug("Setting alerts")
        alerts = CurrentAlerts()
        functions = {"sol": 15, "sul": 14, "bol": 13, "bul": 12, "pol": 11}

        alerts.as_byte = 1 << functions[alert]

        alerts.conv_watch = ready
        alerts.invert = invert
        alerts.latch = latch

        self._write_register("alert_reg", alerts.as_byte)

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
        self._logger.debug("Alert detected")

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
        self._logger.debug("Getting alert flags")
        alerts = CurrentAlerts()
        alerts.as_byte = self._read_register("alert_reg", signed=False)
        flags = {"aff": alerts.alert_func,
                 "cvrf": alerts.conv_flag,
                 "ovf": alerts.overflow}

        # Clear aff bit in the register.
        alerts.alert_func = 0
        self._write_register("alert_reg", alerts.as_byte)

        return flags

class IMU(object):
    def __init__(self, settings_file=None, address=None, name="MPU-9150"):
        if settings_file is None:
            settings_file = "RTIMULib"

        settings = RTIMU.Setings(settings_file)
        if address is not None:
            settings.I2CAddress = address
        self._logger = logging.getLogger("imu-{name}-{address}".format(
            name=name, address=hex(settings.I2CAddress)))
        self._logger.debug("Setting up IMU")
        self._imu = RTIMU.RTIMU(settings)
        self._logger.debug("IMU Name: {}".format(self._imu.IMUName()))
        if not self._imu.IMUInit():
            self._logger.warning("IMU init failed")
        else:
            self._logger.info("IMU has been set up")

        self.poll_interval = self._imu.IMUGetPollInterval()
        self._logger.debug("Recommended poll interval: {} ms".format(
            self.poll_interval))
        self.name = name

    @property
    def rpy(self):
        return self._imu.getFusionData()

