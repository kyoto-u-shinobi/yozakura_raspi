from nose.tools import assert_equal

from rpi.bitfields import ArmPacket, CurrentAlerts, CurrentConfiguration,\
    MotorPacket


def test_arm_packet():
    packet = ArmPacket()
    packet.as_byte = 2**8 - 1
    assert_equal(packet._anonymous_, "b")
    assert_equal(packet.mode.bit_length(), 2)
    assert_equal(packet.linear.bit_length(), 2)
    assert_equal(packet.pitch.bit_length(), 2)
    assert_equal(packet.yaw.bit_length(), 2)


def test_current_alerts():
    packet = CurrentAlerts()
    packet.as_byte = 2**16 - 1
    assert_equal(packet._anonymous_, "b")
    assert_equal(packet.shunt_ol.bit_length(), 1)
    assert_equal(packet.shunt_ul.bit_length(), 1)
    assert_equal(packet.bus_ol.bit_length(), 1)
    assert_equal(packet.bus_ul.bit_length(), 1)
    assert_equal(packet.power_ol.bit_length(), 1)
    assert_equal(packet.conv_watch.bit_length(), 1)
    assert_equal(packet.empty.bit_length(), 5)
    assert_equal(packet.alert_func.bit_length(), 1)
    assert_equal(packet.conv_flag.bit_length(), 1)
    assert_equal(packet.overflow.bit_length(), 1)
    assert_equal(packet.invert.bit_length(), 1)
    assert_equal(packet.latch.bit_length(), 1)


def test_current_configuration():
    packet = CurrentConfiguration()
    packet.as_byte = 2**16 - 1
    assert_equal(packet._anonymous_, "b")
    assert_equal(packet.reset.bit_length(), 1)
    assert_equal(packet.empty.bit_length(), 3)
    assert_equal(packet.avg.bit_length(), 3)
    assert_equal(packet.bus_ct.bit_length(), 3)
    assert_equal(packet.shunt_ct.bit_length(), 3)
    assert_equal(packet.mode.bit_length(), 3)


def test_motor_packet():
    packet = MotorPacket()
    packet.as_byte = 2**8 - 1
    assert_equal(packet._anonymous_, "b")
    assert_equal(packet.motor_id.bit_length(), 2)
    assert_equal(packet.negative.bit_length(), 1)
    assert_equal(packet.speed.bit_length(), 5)
