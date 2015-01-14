// (C) 2015  Kyoto University Mechatronics Laboratory
// Released under the GNU General Public License, version 3
#include "mbed.h"

Serial rpi(USBTX, USBRX);  // USB port acts as a serial connection with rpi.

// Class representing a motor driver.
// 
// Connect the Enable, PWMP, and PWMN pins to the mbed. The motor driver's
// fault signal should go to the Raspberry Pi. Ground can be connected to
// either.
// 
// Sample usage:
//   Motor motor(p21, p11, p12);
//   motor.drive(0.5)  // Runs motor forward at 50% speed.
//   motor.drive(-0.5)  // Runs motor backwards at 50% speed.
class Motor {
  public:    
    // Initialize the motor.
    //
    // Args:
    //   pin_enable: The motor driver's enable pin. In order to have PWM output,
    //     the pin should be between 21 and 26
    //   pin_pos: The motor driver's PWMP pin.
    //   pin_neg: The motor driver's PWMN pin.
    Motor(PinName pin_enable, PinName pin_pos, PinName pin_neg)
        : enable(pin_enable), pos(pin_pos),  neg(pin_neg) {
      enable = pos = neg = 0;  // Set all outputs to low.
      enable.period_us(40);  // Set PWM output frequency to 25 kHz.
    }

    // Drive the motor at the given speed.
    //
    // This works by setting PWMP and PWMN to either high or low depending on
    // the direction the motor turns, and outputting a PWM signal to the motor
    // driver's enable pin.
    //
    // Args:
    //   speed: A value between -1 and 1, representing the speed of the motor.
    void drive(float speed) {
      pos = (speed < 0 ? 0 : 1);
      neg = (speed < 0 ? 1 : 0);
      enable = abs(speed);
    }
    
  private:
    // Variables:
    //   enable: PwmOut for the motor driver's enable pin.
    //   pos: DigitalOut for the motor driver's PWMP pin.
    //   neg: DigitalOut for the motor driver's PWMN pin.
    PwmOut enable;
    DigitalOut pos, neg;
};

int main() {
  // The four motors are in an array. The raspberry pi expects this order, so
  // do not change it without changing the code for the pi as well.
  Motor motors[4] = { Motor(p21, p11, p12),    // Left wheel
                      Motor(p22, p13, p14),    // Right wheel; PWMP and PWMN
                                               //   are physically switched.
                      Motor(p23, p27, p28),    // Left flipper
                      Motor(p24, p29, p30) };  // Left flipper

  char c;
  int motor_id, sign, speed;

  while(1) {
    c = rpi.getc();  // Get byte from rpi.
        
    motor_id = c >> 6;               // First two bits represent the motor ID.
    sign = (c & (1 << 5)) ? -1 : 1;  // Third bit represents the sign of speed.
    speed = c & 31;                  // [0:31], corresponding to [0:1] input.

    motors[motor_id].drive(sign * speed / 31.0);
  }
}
