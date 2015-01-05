// host terminal LED dimmer control
#include "mbed.h"
Serial pc(USBTX, USBRX); // tx, rx
PwmOut motor_1_forward_pin(p21);
PwmOut motor_1_reverse_pin(p22);


void drive_motor(float speed) {  // Assume only motor 1 here.
    if(speed < 0) {
        motor_1_forward_pin = 0;
        motor_1_reverse_pin = -speed;
    }
    else {
        motor_1_forward_pin = speed;
        motor_1_reverse_pin = 0;
    }
}

int main() {
    float speed=0.0;
    char c;
    pc.printf("Control of motor speed by host terminal\n\r");
    pc.printf("Press 'w' = faster, 's' = slower\n\r");
    while(1) {
        c = pc.getc();
        wait(0.1);
        if((c == 'w') && (speed < 1)) {
            speed += 0.1;
            drive_motor(speed);
        }
        else if((c == 's') && (speed > -1)) {
            speed -= 0.1;
            drive_motor(speed);
        }
        else if(c == '0') {
            while(speed != 0) {
                speed -= 0.1 * (speed > 0 ? 1 : -1);
                drive_motor(speed);
                wait(0.1);
            }
        }
        pc.printf("%c %1.3f \n \r",c,speed);
    }
}