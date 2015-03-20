// (C) 2015 Kyoto University Mechatronics Laboratory
// Released under the GNU General Public License, version 3
#include "mbed.h"
#include "motor.h"

int main() {
    // The four motors are in an array. The raspberry pi expects this order;
    // do not change it without changing the code for the rpi as well.
    Motor motors[4] = { Motor(p21, p11),   // Left wheels
                        Motor(p22, p12),   // Right wheels
                        Motor(p23, p13),   // Left flipper
                        Motor(p24, p14) }; // Right flipper
    
    // Set up ADC ports. If you add ADC devices, please add them in order
    // from the lowest pin to the highest.
    AnalogIn pots[6] = {p15, p16, p17, p18,  // Unused 
                        p19,                 // Left flipper position
                        p20};                // Right flipper position
    
    int n_adc = 2; // Number of ADC Channels in use. Max is 6.
    uint16_t adc_results[n_adc];
    for (int i = 0; i < n_adc; i++) {
        adc_results[i] = 0; // Zero the results.
    }
    
    union MotorPacket packet;
    int sign;
    
    while(1) {
        // Drive the motor
        if(rpi.readable()) {
            packet.as_byte = rpi.getc(); // Get packet from rpi.
        }

        // If speed is 0 but negative is true, you can consider these as special
        // requests, and you may do whatever you want. Since there is a maximum
        // of 4 motor IDs, you can use a switch statement.
        // 
        // It is best if you write a function and simply call it from here.
        //
        // Uncomment this code to use it.
        if(packet.b.negative and !packet.b.speed) {
        /*
            switch(packet.b.motor_id) {
                case 0:
                    // Code
                    break;
                case 1:
                    // Code
                    break;
                case 2:
                    // Code
                    break;
                case 3:
                    // Code
                    break;
            }
        */
        }
        else { // Drive motor.
            sign = packet.b.negative ? -1 : 1;
            motors[packet.b.motor_id].drive(sign * packet.b.speed / 31.0);
        }

        // Update extra ADC results.
        for(int i = 0; i < n_adc - 2; i++)
        {
            adc_results[i] = pots[i].read_u16();
        }
        
        adc_results[n_adc - 2] = pots[4].read_u16();  // Left flipper position
        adc_results[n_adc - 1] = pots[5].read_u16();  // Right flipper position

        // Send data to Rpi.
        for(int i = 0; i < n_adc; i++) {
            rpi.printf("0x%X ", adc_results[i]);
        }

        rpi.printf("\n");
    }
}
