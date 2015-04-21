#ifndef MBED_MEMS_H
#define MBED_MEMS_H

#include "mbed.h"

#define D6T_addr 0x14
#define D6T_cmd  0x4c

class MEMS {
 public:
  /* @param sda : I2C pin
     @param scl : I2C pin
  */
  MEMS(PinName sda, PinName scl);

  /*
     @param datr : temperature data[16]
  */    
  void temp(float* datr);

 private:
  I2C _mems;
};

#endif
