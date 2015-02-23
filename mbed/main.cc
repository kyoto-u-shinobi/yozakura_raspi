// (C) 2015  Kyoto University Mechatronics Laboratory
// Released under the GNU General Public License, version 3
#include "mbed.h"


Serial rpi(USBTX, USBRX);  // USB port acts as a serial connection with rpi.


// A bitfield representing the motor packet received from the rpi.
//
// The first two bits of the packet represent the motor ID, between 0 and 3.
// The third bit is the sign, with a value of 1 when negative and 0 when
// positive. The last five bits represent the speed, with a value between 0
// and 31. [0:31] corresponds to a [0:1] requested speed.
struct MotorPacket {
  unsigned int motor_id : 2;
  unsigned int negative : 1;
  unsigned int speed : 5;
};


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
  // do not change it without changing the code for the pi as well. Note that
  // in the prototype robot, the polarity of the right wheel has been flipped.
  Motor motors[4] = { Motor(p21, p11, p12),    // Left wheel
                      Motor(p22, p13, p14),    // Right wheel
                      Motor(p23, p27, p28),    // Left flipper
                      Motor(p24, p29, p30) };  // Left flipper

  MotorPacket packet;
  int sign;

  while(1) {
    packet = rpi.getc();  // Get packet from rpi.
    sign = packet.negative ? -1 : 1;

    motors[packet.motor_id].drive(sign * packet.speed / 31.0);  // Drive!
  }
}
