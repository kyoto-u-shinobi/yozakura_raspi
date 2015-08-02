 /* mbed Microcontroller Library
 * Copyright (c) 2006-2012 ARM Limited
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in
 * all copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 * NOTE: This is an unsupported legacy untested library.
 */
#include "SerialHalfDuplex.h"
 
#if DEVICE_SERIAL
 
#include "pinmap.h"
#include "serial_api.h"
#include "gpio_api.h"
//#include "RawSerial.h"
 
namespace mbed {
 
SerialHalfDuplex::SerialHalfDuplex(PinName tx, PinName rx, const char *name)
    : Serial(tx, rx, name) {
    _txpin = tx;
    
    // set as input 
    gpio_set(_txpin); 
    pin_mode(_txpin, PullNone); // no pull
    pin_function(_txpin, 0);    // set as gpio
}
 
// To transmit a byte in half duplex mode:
// 1. Disable interrupts, so we don't trigger on loopback byte
// 2. Set tx pin to UART out
// 3. Transmit byte as normal
// 4. Read back byte from looped back tx pin - this both confirms that the
//    transmit has occurred, and also clears the byte from the buffer.
// 5. Return pin to input mode
// 6. Re-enable interrupts
 
int SerialHalfDuplex::_putc(int c) {
    int retc;
    
    // TODO: We should not disable all interrupts
    __disable_irq();
    
    serial_pinout_tx(_txpin);
    
    Serial::_putc(c);
    retc = Serial::getc();       // reading also clears any interrupt
    
    pin_function(_txpin, 0);
    
    __enable_irq();
    
    return retc;
}
 
int SerialHalfDuplex::_getc(void) {
    return Serial::_getc();
}
 
} // End namespace
 
#endif
