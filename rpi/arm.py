# (C) 2015  Kyoto University Mechatronics Laboratory
# Released under the GNU General Public License, version 3
import logging
import time


class Arm(object):
    servos = []
    
    def __init__(self):
        self._logger = logging.getLogger("Arm")
        self._logger.debug("Arm created")
        self._positions = [None, None, None]
    
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
            servo.upstep = upstep
            servo.downstep = downstep
            
            self.servos.append(servo)
            self._logger.info("Servo added")
            if len(self.servos) == 3:
                self._positions = self._update_positions()
    
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
    
    def get_data(self):
        #self._positions = self._update_positions()
        values = [self.servos[0].voltage] + [servo.current for servo in self.servos[1:]]
        return self._positions, values
    
    def handle_commands(self, commands):
        print(commands)
        if all(not i for i in commands):
            return
        mode, *inputs = commands

        self._positions = self._update_positions()
        
        if mode == 0:
            for servo, command, position in zip(self.servos, inputs, self._positions):
                servo.torque_limit = 1023
                if servo.name == "yaw":
                    print("Yaw!")
                if command == 0:
                    servo.goal = position
                elif command == 1:
                    servo.goal = max(servo.cw_limit, position - servo.downstep)
                elif command == -1:
                    servo.goal = min(servo.ccw_limit, position + servo.upstep)
                else:
                    self._logger.error("Invalid command received: {cmd}".format(cmd=commands))
                if servo.name == "yaw":
                    print(servo.goal)
        elif mode == 1:
            self.go_home()
        elif mode == 2:
            self.reset()
        elif mode == 3:
            self.end()
        else:
            self._logger.error("Invalid command received: {cmd}".format(cmd=commands))
    
    @property
    def is_moving(self):
        return any(servo.is_moving for servo in self.servos)
    
    def wait_until_stopped(self):
        while self.is_moving:
            pass
    
    def _update_positions(self):
        return [servo.position for servo in self.servos]
    
    def _power_down(self):
        for servo in self.servos:
            servo.torque_limit = 0
    
    def _power_up(self):
        for servo in self.servos:
            servo.torque_limit = 1023
    
    def __repr__(self):
        return "{n}-servo arm".format(n=len(self.servos))
    
    def __str__(self):
        return self.__repr__()
