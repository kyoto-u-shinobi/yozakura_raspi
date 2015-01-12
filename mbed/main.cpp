// (C) 2015  Kyoto University Mechatronics Laboratory
// Released under the GNU General Public License, version 3
#include "mbed.h"

Serial rpi(USBTX, USBRX);

class Motor {
  public:    
    Motor(PinName pin_enable, PinName pin_pos, PinName pin_neg) : enable(pin_enable), pos(pin_pos),  neg(pin_neg) {
        enable = pos = neg = 0;
    }

    void drive(float speed) {
      pos = (speed < 0 ? 0 : 1);
      neg = (speed < 0 ? 1 : 0);
      enable = abs(speed);
    }
    
  private:
    PwmOut enable;
    DigitalOut pos, neg;
};

int main() {
    Motor motors[4] = { Motor(p21, p11, p12),
                        Motor(p22, p13, p14), 
                        Motor(p23, p27, p28), 
                        Motor(p24, p29, p30) };

    char c;
    int motor_id, sign, speed;

    while(1) {
        c = rpi.getc();
        
        motor_id = c >> 6;
        sign = (c & (1 << 5)) ? -1 : 1;
        speed = c & 31;

        motors[motor_id].drive(sign * speed / 31.0);
    }
}
