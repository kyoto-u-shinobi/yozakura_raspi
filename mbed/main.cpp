// (C) 2015  Kyoto University Mechatronics Laboratory
// Released under the GNU General Public License, version 3
#include "mbed.h"

Serial rpi(USBTX, USBRX);

class Motor {
  PwmOut enable;
  DigitalOut pos, neg;
  public:
    Motor(PinName pin_enable, PinName pin_pos, PinName pin_neg) {
      enable(pin_enable);
      pos(pin_pos);
      neg(pin_neg);
    }

    void drive(float speed) {
      pin_pos = (speed < 0 ? 0 : 1);
      pin_pos = (speed < 0 ? 1 : 0);
      enable = speed;
    }
};

Motor * motors;
motors = new Motor[4] { {p21, p11, p12},  // left motor
			{p22, p13, p14},  // right motor
			{p23, p27, p28},
			{p24, p29, p30} };

int main() {
  char c;
  int motor, sign, speed;
  while(1) {
    c = pc.getc();

    motor = c >> 6;
    sign = (c & (1 << 5)) ? -1 : 1;
    speed = c & 31;

    motors[motor].drive(sign * speed / 31);
  }

  return 0;
}
