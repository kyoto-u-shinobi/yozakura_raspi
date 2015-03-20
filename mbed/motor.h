// (C) 2015 Kyoto University Mechatronics Laboratory
// Released under the GNU General Public License, version 3
#ifndef MOTOR_H
#define MOTOR_H

#include "mbed.h"
// A bitfield representing the motor packet received from the rpi.
//
// The first two bits of the packet represent the motor ID, between 0 and 3.
// The third bit is the sign, with a value of 1 when negative and 0 when
// positive. The last five bits represent the speed, with a value between 0
// and 31. [0:31] corresponds to a [0:1] requested speed.
//
// If the sign is 1 and the speed is zero, the motor ID of the packet is
// instead used to request updated data from up to four ADC channels.
struct MotorPacketBits {
                        unsigned int motor_id : 2;
                        unsigned int negative : 1;
                        unsigned int speed : 5;
                       };

union MotorPacket {
                   struct MotorPacketBits b;
                   unsigned char as_byte;
                  };
     
                  
// Class representing a motor driver.
//
// Connect the PWM and DIR pins to the mbed. The motor driver's fault signals
// should go to the Raspberry Pi. Ground can be connected to
// either.
//
// Datasheet: https://www.pololu.com/product/755
//
// Sample usage:
// Motor motor(p21, p11);
// motor.drive(0.5) // Runs motor forward at 50% speed.
// motor.drive(-0.5) // Runs motor backwards at 50% speed.
class Motor {
    private:
        PwmOut pwm;      // PwmOut for the motor driver's PWM pin.
        DigitalOut dir;  // DigitalOut for the motor driver's direction pin.

    public:
        // Initialize the motor.
        //
        // Args:
        // pin_pwm: The motor driver's PWM pin. In order to have PWM output,
        // the pin should be between 21 and 26.
        // pin_dir: The motor driver's DIR pin. HI is forward, LO is reverse.
        Motor(PinName pin_pwm, PinName pin_dir);
        
        // Drive the motor at the given speed.
        //
        // Args:
        // speed: A value between -1 and 1, representing the speed of the motor.
        void drive(float speed);
};

#endif
