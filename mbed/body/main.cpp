// (C) 2015 Kyoto University Mechatronics Laboratory
// Released under the GNU General Public License, version 3
#include "mbed.h"

Serial rpi(USBTX, USBRX); // USB port acts as a serial connection with rpi.

// A bitfield representing the motor packet received from the rpi.
//
// The first two bits of the packet represent the motor ID, between 0 and 3.
// The third bit is the sign, with a value of 1 when negative and 0 when
// positive. The last five bits represent the speed, with a value between 0
// and 31. [0:31] corresponds to a [0:1] requested speed.
//
// If the sign is 1 and the speed is zero, the packet can instead be used for
// running up to four functions based on the Motor ID.
//
// Note that bitfields on the mbed are little endian by default.
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
// should go to the Raspberry Pi. Ground can be connected to either.
//
// Datasheet: https://www.pololu.com/product/755
//
// Examples:
//     Motor motor(p21, p11);
//     motor.drive(0.5) // Runs motor forward at 50% speed.
//     motor.drive(-0.5) // Runs motor backwards at 50% speed.
class Motor {
 public:
  // Initialize the motor.
  //
  // Parameters:
  //   pin_pwm: The motor driver's PWM pin. In order to have PWM output, the
  //            pin should be between 21 and 26.
  //   pin_dir: The motor driver's DIR pin. If the driver is not connected in
  //            reverse, HI is forward, and LO is reverse.
  //   reversed: Whether the motor driver's DIR pin is connected in reverse.
  Motor(PinName pin_pwm, PinName pin_dir, bool reversed)
      : pwm_(pin_pwm), dir_(pin_dir), reversed_(reversed) {
    pwm_ = 0;
    dir_ = 0;
    pwm_.period_us(40);  // Set PWM output frequency to 25 kHz.
  }

  // Drive the motor at the given speed.
  //
  // Parameters:
  //   speed: A value between -1 and 1, representing the motor speed.
  void drive(float speed) {
    if (reversed_) {
      dir_ = speed < 0 ? 1 : 0;
    } else {
      dir_ = speed < 0 ? 0 : 1;
    }
    pwm_ = abs(speed);
  }

 private:
    PwmOut pwm_;      // The motor driver's PWM pin.
    DigitalOut dir_;  // The motor driver's DIR pin.
    bool reversed_;   // Whether DIR is connected in reverse.
};


int main() {
  // The four motors are in an array. The raspberry pi expects this order; do
  // not change it without changing the code for the RPi as well.
  Motor motors[4] = { Motor(p26, p27, false),     // Left wheels
                      Motor(p25, p28, true),      // Right wheels
                      Motor(p24, p29, true),      // Left flipper
                      Motor(p23, p30, false) };   // Right flipper

  AnalogIn pots[6] = { p15, p16, p17, p18,   // Unused
                       p19,                  // Left flipper position
                       p20 };                // Right flipper position

  int n_adc = 2; // Number of ADC Channels in use. Max is 6.
  uint16_t adc_results[n_adc];
  for (int i = 0; i < n_adc; i++) {
    adc_results[i] = 0; // Zero the results.
  }

  union MotorPacket packet;
  int sign;

  rpi.baud(38400);  // Match this in the RPi settings.

  while(1) {
    // Get packet from RPi.
    if(rpi.readable()) {
      packet.as_byte = rpi.getc();
    }

    if(packet.b.motor_id == 3 and packet.b.negative and not packet.b.speed) {
      rpi.printf("body\n")
    } else {
      // Drive motor.
      sign = packet.b.negative ? -1 : 1;
      motors[packet.b.motor_id].drive(sign * packet.b.speed / 31.0);

      // Update flipper positions.
      adc_results[n_adc - 2] = pots[4].read_u16();  // Left flipper position
      adc_results[n_adc - 1] = pots[5].read_u16();  // Right flipper position

      // Send data to RPi.
      for(int i = 0; i < n_adc; i++) {
        rpi.printf("%X ", adc_results[i]);
      }
      rpi.printf("\n");
    }
  }
}
