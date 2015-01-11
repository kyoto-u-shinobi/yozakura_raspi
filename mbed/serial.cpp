#include "mbed.h"

DigitalOut myled(LED1);
Serial rpi(USBTX, USBRX);

int main() {
    char ch;
    while(1) {
        ch = rpi.getc();
        if (ch == 'a') myled = 1;
        else myled = 0;
    }
}
