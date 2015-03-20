#ifndef PINS_H
#define PINS_H

#include "motor.h"
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
    
#endif
