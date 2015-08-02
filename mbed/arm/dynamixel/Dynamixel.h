/* mbed Dynamixel Servo Library
 *
 * Copyright (c) 2015, Jean Nassar
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
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
 * THE SOFTWARE.
 */
#ifndef MBED_DYNAMIXEL_H
#define MBED_DYNAMIXEL_H

#include "mbed.h"
#include "SerialHalfDuplex.h"

#define AX12_WRITE_DEBUG 0
#define AX12_READ_DEBUG 0
#define AX12_TRIGGER_DEBUG 0
#define AX12_DEBUG 0

#define AX12_REG_ID 0x3
#define AX12_REG_CW_LIMIT 0x06
#define AX12_REG_CCW_LIMIT 0x08
#define AX12_REG_TORQUE_ENABLE 0x18
#define AX12_REG_GOAL_POSITION 0x1E
#define AX12_REG_MOVING_SPEED 0x20
#define AX12_REG_VOLTS 0x2A
#define AX12_REG_TEMP 0x2B
#define AX12_REG_MOVING 0x2E
#define AX12_REG_TORQUE_LIMIT 0x22
#define AX12_REG_POSITION 0x24

#define AX12_MODE_POSITION  0
#define AX12_MODE_ROTATION  1

#define AX12_CW 1
#define AX12_CCW 0

#define MX28_WRITE_DEBUG 0
#define MX28_READ_DEBUG 0
#define MX28_TRIGGER_DEBUG 0
#define MX28_DEBUG 0

#define MX28_REG_ID 0x3
#define MX28_REG_CW_LIMIT 0x06
#define MX28_REG_CCW_LIMIT 0x08
#define MX28_REG_TORQUE_ENABLE 0x18
#define MX28_REG_GOAL_POSITION 0x1E
#define MX28_REG_MOVING_SPEED 0x20
#define MX28_REG_VOLTS 0x2A
#define MX28_REG_TEMP 0x2B
#define MX28_REG_MOVING 0x2E
#define MX28_REG_POSITION 0x24
#define MX28_REG_TORQUE_LIMIT 0x22
#define MX28_REG_CURRENT 0x44

#define MX28_MODE_POSITION  0
#define MX28_MODE_ROTATION  1

#define MX28_CW 1
#define MX28_CCW 0

/** Servo control class, based on a PwmOut
 *
 * Example:
 * @code
 * #include "mbed.h"
 * #include "AX12.h"
 * 
 * int main() {
 * 
 *   AX12 myax12 (p9, p10, 1);
 *
 *   while (1) {
 *       myax12.SetGoal(0);    // go to 0 degrees
 *       wait (2.0);
 *       myax12.SetGoal(300);  // go to 300 degrees
 *       wait (2.0);
 *   }
 * }
 * @endcode
 */
class Dynamixel {

public:



    /** Set the mode of the servo
     * @param mode
     *    0 = Positional, default
     *    1 = Continuous rotation
     */
    virtual int SetMode(int mode) {return 0;}

    /** Set goal angle in integer degrees, in positional mode
     *
     * @param degrees 0-300
     * @param flags, defaults to 0
     *    flags[0] = blocking, return when goal position reached 
     *    flags[1] = register, activate with a broadcast trigger
     *
     */
    virtual int SetGoal(int degrees, int flags = 0) {return 0;}


    /** Set the speed of the servo in continuous rotation mode
     *
     * @param speed, -1.0 to 1.0
     *   -1.0 = full speed counter clock wise
     *    1.0 = full speed clock wise
     */
    virtual int SetCRSpeed(float speed) {return 0;}


    /** Set the clockwise limit of the servo
     *
     * @param degrees, 0-300
     */
    virtual int SetCWLimit(int degrees) {return 0;}
    
    /** Set the counter-clockwise limit of the servo
     *
     * @param degrees, 0-300
     */
    virtual int SetCCWLimit(int degrees) {return 0;}

    // Change the ID

    /** Change the ID of a servo
     *
     * @param CurentID 1-255
     * @param NewID 1-255
     *
     * If a servo ID is not know, the broadcast address of 0 can be used for CurrentID.
     * In this situation, only one servo should be connected to the bus
     */
    virtual int SetID(int CurrentID, int NewID) {return 0;}


    /** Poll to see if the servo is moving
     *
     * @returns true is the servo is moving
     */
    virtual int isMoving(void) {return 0;}

    /** Send the broadcast "trigger" command, to activate any outstanding registered commands
     */
    virtual void trigger(void) {}

    /** Read the current angle of the servo
     *
     * @returns float in the range 0.0-300.0
     */
    virtual float GetPosition() {return 0;}

    /** Read the temperature of the servo
     *
     * @returns float temperature 
     */
    virtual float GetTemp(void) {return 0;}

    /** Read the supply voltage of the servo
     *
     * @returns float voltage
     */
    virtual float GetVolts(void) {return 0;}
    virtual float GetCurrent(void) {return 0;}
    
    virtual int TorqueEnable(int mode) {return 0;}
    
    virtual int SetTorqueLimit(float torque_limit) {return 0;}

protected :
    int _ID;

    virtual int read(int ID, int start, int length, char* data) {return 0;}
    virtual int write(int ID, int start, int length, char* data, int flag=0) {return 0;}

};

class AX12 : public Dynamixel {
 public:
  /** Create a Dynamixel servo object connected to the specified serial port, with the specified ID
  *
  * @param pin tx pin
  * @param pin rx pin 
  * @param int ID, the Bus ID of the servo 1-255 
  */
  AX12(PinName tx, PinName rx, int ID);
  
  virtual int SetMode(int mode);
  virtual int SetGoal(int degrees, int flags = 0);
  virtual int SetCRSpeed(float speed);
  virtual int SetCWLimit(int degrees);
  virtual int SetCCWLimit(int degrees);
  virtual int SetID(int CurrentID, int NewID);
  virtual int isMoving(void);
  virtual void trigger(void);
  virtual float GetPosition();
  virtual float GetTemp(void);
  virtual float GetVolts(void);
  virtual int TorqueEnable(int mode);
  virtual int SetTorqueLimit(float torque_limit);
  virtual float GetCurrent(void);
 
 protected:
  virtual int read(int ID, int start, int length, char* data);
  virtual int write(int ID, int start, int length, char* data, int flag=0);
 
 private:
  SerialHalfDuplex _ax12;
};

class MX28 : public Dynamixel {
 public:
  /** Read the supply current of the servo
   *
   * @returns float current
   */
  MX28(PinName tx, PinName rx, int ID);
  
  virtual int SetMode(int mode);
  virtual int SetGoal(int degrees, int flags = 0);
  virtual int SetCRSpeed(float speed);
  virtual int SetCWLimit(int degrees);
  virtual int SetCCWLimit(int degrees);
  virtual int SetID(int CurrentID, int NewID);
  virtual int isMoving(void);
  virtual void trigger(void);
  virtual float GetPosition();
  virtual float GetTemp(void);
  virtual float GetVolts(void);
  virtual int TorqueEnable(int mode);
  virtual int SetTorqueLimit(float torque_limit);
  
  /** Create a Dynamixel servo object connected to the specified serial port, with the specified ID
  *
  * @param pin tx pin
  * @param pin rx pin 
  * @param int ID, the Bus ID of the servo 1-255 
  */
  virtual float GetCurrent(void);

 protected:
  virtual int read(int ID, int start, int length, char* data);
  virtual int write(int ID, int start, int length, char* data, int flag=0);
 
 private:
  SerialHalfDuplex _mx28;
};

#endif
