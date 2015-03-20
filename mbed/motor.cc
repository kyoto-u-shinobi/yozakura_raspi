// (C) 2015 Kyoto University Mechatronics Laboratory
// Released under the GNU General Public License, version 3
#include "motor.h"

Motor::Motor(PinName pin_pwm, PinName pin_dir) : pwm(pin_pwm), dir(pin_dir) {
    pwm = dir = 0; // Set all outputs to low.
    pwm.period_us(40); // Set PWM output frequency to 25 kHz.
}

void Motor::drive(float speed) {
    dir = speed < 0 ? 0 : 1;
    pwm = abs(speed);
}
