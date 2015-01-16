import unittest
from ..rpi/devices import CurrentSensor

class TestCurrentSensor(unittest.TestCase):
    def setUp(self):
        self.sensor = CurrentSensor(0x40, name="current_sensor")

    def test_get_configuration(self):
        pass

    def test_set_configuration(self):
        pass

    def test_rest(self):
        pass

    def test_get_measurement_dne(self):
        pass

    def test_get_measurement_no_calib(self):
        pass

    def test_get_current(self):
        pass

    def test_get_power(self):
        pass

    def test_get_v_shunt(self):
        pass

    def test_get_v_bus(self):
        pass

    def test_calibrate(self):
        pass

    def test_set_alerts(self):
        pass

    def test_interrupts(self):
        pass
    
    def test_get_alerts(self):
        pass

    def test_get_alerts_resets(self):
        pass

    def tearDown(self):
        pass
