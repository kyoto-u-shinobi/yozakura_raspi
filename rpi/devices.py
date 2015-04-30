# (C) 2015  Kyoto University Mechatronics Laboratory
# Released under the GNU General Public License, version 3
"""
Functions and classes for using I2C devices.

Provides functions to simplify work with I2C devices, as well as classes for
each attached device. The following devices are currently supported:

- Texas Instruments INA226 Current/Power Monitor [#]_
- Invenense MPU-9150 9-axis MEMS MotionTracking Device [#]_

References
----------
.. [#] Texas Instruments, INA 226 datasheet.
       http://www.ti.com/lit/ds/symlink/ina226.pdf

.. [#] Invensense, MPU-9150 Product Specification.
       http://www.invensense.com/mems/gyro/documents/PS-MPU-9150A-00v4_3.pdf

"""
from collections import OrderedDict
import logging
import re
import subprocess

from RPi import GPIO as gpio
import RTIMU
import smbus

from common.exceptions import BadArgError, I2CSlotEmptyError,\
    I2CSlotBusyError, NotCalibratedError
from rpi.bitfields import CurrentConfiguration, CurrentAlerts


class Device(object):
    """
    Parent class for all I2C devices. Provides registration and deregistration.

    Parameters
    ----------
    address : int
        The address of the i2c device.
    name : str
        The name of the device.

    Raises
    ------
    I2CSlotEmptyError
        No devices could be found at the specified address.
    I2CSlotBusyError
        The address is valid, but another device has already been registered at
        that address and has not been removed yet.

    Attributes
    ----------
    address : int
        The address of the I2C device.
    name : str
        The name of the device.
    devices : dict
        Contains all registered devices.

        Dictionary format: {address (str): device (Device)}

    """
    devices = {}
    _i2c_bus = None

    def __init__(self, address, name):
        self._logger = logging.getLogger("i2c-{name}-{address}"
                                         .format(name=name,
                                                 address=hex(address)))
        if Device._i2c_bus is None:
            Device._i2c_bus = self._get_i2c_bus()  # /dev/i2c-0 or /dev/i2c-1

        self._logger.debug("Initializing device")
        slots = self._get_used_i2c_slots()
        if address not in slots:
            raise I2CSlotEmptyError(address)
        elif slots[address] == "UU" or address in Device.devices.values():
            raise I2CSlotBusyError(address)

        else:  # Everything is fine.
            self.address = address
            self.name = name
            self.bus = smbus.SMBus(Device._i2c_bus)
            Device.devices[address] = self
        self._logger.info("Device initialized")

    @staticmethod
    def _get_i2c_bus():
        """
        Detect the revision number of a Raspberry Pi, useful for changing
        functionality like default I2C bus based on revision. The revision list
        is available online. [#]_

        Revision 1 pi uses I2C Bus 0, while revision 2 uses I2C Bus 1.

        This function is based on an Adafruit I2C implementation. [#]_

        References
        ----------
        .. [#] ELinux.org. "RPi Hardware History."
               http://elinux.org/RPi_HardwareHistory#Board_Revision_History
        .. [#] Adafruit Python GPIO, Adafruit, Github. "Platform.py"
               https://github.com/adafruit/Adafruit_Python_GPIO/blob/master/Adafruit_GPIO/Platform.py#L53

        """
        with open("/proc/cpuinfo", "r") as infile:
            for line in infile:
                # Match a line of the form "Revision : 0002" while ignoring
                # info in front of the revsion (like 1000 when overvolted).
                match = re.match("Revision\s+:\s+.*(\w{4})$", line,
                                 flags=re.IGNORECASE)
                if match and match.group(1) in ["0000", "0002", "0003"]:
                    return 0  # Revision 1
                elif match:
                    return 1  # Revision 2
            # Couldn't find the revision, throw an exception.
            raise RuntimeError('Could not determine Raspberry Pi revision.')

    @staticmethod
    def _get_used_i2c_slots():
        """
        Find all used i2c slots.

        This function calls an external ``i2cdetect`` command, and works on the
        resultant table to find out which slots are occupied.

        Returns
        -------
        slots : dict
            Contains all used i2c slots and their values.

            **Dictionary format :** {slot_number (int): slot_number_hex (str)}

        """
        slots = OrderedDict()
        command = "i2cdetect -y {bus}".format(bus=Device._i2c_bus)
        table = subprocess.check_output(command.split()).splitlines()[1:]
        for i, row in enumerate(table):
            row = str(row, encoding="utf-8")
            for j, item in enumerate(row.split()[1:]):
                if item != "--":
                    slots[16*i + (j if i > 0 else j + 3)] = item
        return slots

    def remove(self):
        """Deregister the device."""
        self._logger.info("Deregistering device")
        del Device.devices[self.address]

    def __repr__(self):
        return "{dev_type} at {addr} ({name})".format(
            dev_type=self.__class__.__name__,
            addr=hex(self.address),
            name=self.name)

    def __str__(self):
        return self.name


class CurrentSensor(Device):
    """
    Texas Instruments INA226 Current/Power Monitor. [#]_

    The current sensor must be calibrated before use.

    Parameters
    ----------
    address : int
        The address of the device.
    name : str, optional
        The name of the device.

    Attributes
    ----------
    address : int
        The address of the device.
    pin_alert : int
        The alert pin of the device. None if not connected.
    name : str
        The name of the device.
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

    Notes
    -----
    All words are big endian.

    References
    ----------
    .. [#] Texas Instruments, INA 226 datasheet.
           http://www.ti.com/lit/ds/symlink/ina226.pdf

    """
    registers = {"config":    0,
                 "v_shunt":   1,
                 "v_bus":     2,
                 "power":     3,
                 "current":   4,
                 "calib":     5,
                 "alert_reg": 6,
                 "alert_lim": 7,
                 "die": 0xFF}

    def __init__(self, address, name="Current Sensor"):
        self.lsbs = {"v_shunt": 2.5e-6,  # Volts
                     "v_bus":  1.25e-3,  # Volts
                     "power":     None,  # Watts
                     "current":   None}  # Amperes

        super().__init__(address, name)
        self.pin_alert = None
        self.calibrate(40.96)  # 40.96 A max current.
        #self.set_configuration(avg=2, bus_ct=3, shunt_ct=3)
        self.set_configuration()

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
        self._logger.debug("Reading {reg} register".format(reg=register))
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
        self._logger.debug("Writing {data} to {reg} register"
                           .format(data=data, reg=register))
        data = int(data)

        # bus.write_word_data writes one byte at a time, so we switch the byte
        # order before writing.
        data = ((data & 0xff) << 8) + (data >> 8)
        self.bus.write_word_data(self.address, self.registers[register], data)

    def get_configuration(self):
        """
        Read the current sensor configuration.

        See pages 18 and 19 in the datasheet [#]_ for more information.

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
        .. [#] Texas Instruments, INA 226 datasheet.
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

        See pages 18 and 19 in the datasheet. [#]_ This function only changes
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
        .. [#] Texas Instruments, INA 226 datasheet.
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
        self._logger.debug("Getting {reg} measurement".format(reg=register))
        # Force a read if triggered mode.
        if 0 < self.get_configuration().mode <= 3:
            self.set_configuration()
        # TODO(masasin): Add a wait for conversion to be complete.

        if register not in self.lsbs:
            raise BadArgError("{reg} is not a measurement!"
                              .format(reg=register))
        try:
            return self._read_register(register) * self.lsbs[register]
        except TypeError:
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

        self.lsbs["current"] = max_current / 2**15      # Amperes
        self.lsbs["power"] = 25 * self.lsbs["current"]  # Watts
        calib_value = 0.00512 / (self.lsbs["current"] * r_shunt)
        self._write_register("calib", calib_value)

    def set_alerts(self, alert, limit,
                   ready=False, invert=False, latch=False,
                   pin_alert=None, interrupt=False):
        """
        Choose the alert function and set up the alert behaviour.

        See pages 21 and 22 of the datasheet [#]_ for more information.

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
        .. [#] Texas Instruments, INA 226 datasheet.
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
            lsb = self.lsbs["v_shunt"]
        elif alert == "bol" or alert == "bul":
            lsb = self.lsbs["v_bus"]
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

    @property
    def iv(self):
        """
        Return the Current and Voltage of the sensor, in natural units.

        Returns
        -------
        CurrentSensorData
            The current and voltage readings of the sensor.

        """
        current = self.get_measurement("current")
        # power = self.get_measurement("power")
        # if current == 0:
        #     voltage = 0
        # else:
        #     voltage = power / current
        voltage = self.get_measurement("v_bus")
        return current, voltage


class IMU(Device):
    """
    Invenense MPU-9150 9-axis MEMS MotionTracking Device. [#]_

    Simple wrapper for the RTIMU library by richards-tech [#]_ for accessing
    the sensor fusion data of the MPU-9150.

    Parameters
    ----------
    settings_file : str, optional
        The location of the settings file, without the ".ini" extension.
    address : int, optional
        The address of the device. If provided, it overrides the I2C address
        found in the settings file.
    name : str, optional
        The name of the device.

    Attributes
    ----------
    address : int
        The address of the device.
    poll_interval : int
        The recommended poll interval, in milliseconds.
    name : str
        The name of the device.

    References
    ----------
    .. [#] Invensense, MPU-9150 Product Specification.
           http://www.invensense.com/mems/gyro/documents/PS-MPU-9150A-00v4_3.pdf
    .. [#] RTIMULib, richards-tech, Github.
           https://github.com/richards-tech/RTIMULib

    """
    def __init__(self, settings_file="imu_settings", address=None,
                 name="MPU-9150"):
        self._settings = RTIMU.Settings(settings_file)
        if address is not None:
            self._settings.I2CAddress = address
        else:
            address = self._settings.I2CAddress

        self._logger = logging.getLogger("imu-{name}-{address}"
                                         .format(name=name,
                                                 address=hex(address)))

        self._imu = RTIMU.RTIMU(self._settings)
        if not self._imu.IMUInit():
            self._logger.warning("IMU init failed")
            return
        else:
            self._logger.info("IMU init succeeded")
        
        self._imu.setCompassEnable(False)  # Check to see if there are big fluctuations.

        self.poll_interval = self._imu.IMUGetPollInterval
        super().__init__(address, name)

    @property
    def rpy(self):
        """
        Return the Roll, Pitch, and Yaw data, in radians.

        Returns
        -------
        IMUData
            The roll, pitch, and yaw readings of the IMU, in radians.

        """
        data = self._imu.getIMUData()
        while self._imu.IMURead():
            data = self._imu.getIMUData()
        if data["fusionPoseValid"]:
            return data["fusionPose"]
        else:
            return [None, None, None]
