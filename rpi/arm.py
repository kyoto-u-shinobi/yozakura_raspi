# (C) 2015  Kyoto University Mechatronics Laboratory
# Released under the GNU General Public License, version 3
import logging

from common.exceptions import DynamixelError
from rpi.dynamixel import AX12, MX28


class Arm(object):
    servos = []
    
    def __init__(self):
        self._logger = logging.getLogger("Arm")
    
    def add_servo(self, servo, home_position=300, limits=(172, 300),
                  speed=100, upstep=1, downstep=1, multiturn=False):
        self._logger.debug("Adding {name}".format(name=servo))
        if servo not in self.servos:
            servo.torque_limit = 0
            servo.moving_speed = speed
            if multiturn:
                servo.engage_multiturn_mode()
            else:
                servo.limits = limits
            servo.home_position = home_position
            
            self.servos.append(servo)
            self._logger.info("Servo added")
    
    def go_home(self):
        self._power_up()
        self.servos[0].goal = self.servos[0].home_position
        if self.servos[0].position > self.servos[0].ccw_limit:
            for servo in servos[1:]:
                servo.goal = servo.home_position
    
    def go_home_loop(self):
        self.go_home()  # Linear
        self.wait_until_stopped
        self.go_home()  # Pitch and yaw
        self.wait_until_stopped
    
    def reset(self):
        self._power_down()
        time.sleep(1)
        self._power_up()
    
    def end(self):
        self._power_down()
    
    @property
    def is_moving(self):
        return any(servo.is_moving for servo in self.servos)
    
    def wait_until_stopped(self):
        while self.is_moving:
            pass
    
    def _power_down(self):
        for servo in self.servos:
            servo.torque_limit = 0
    
    def _power_up(self):
        for servo in self.servos:
            servo.torque_limit = 1023
