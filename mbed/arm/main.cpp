// (C) 2015 Kyoto University Mechatronics Laboratory
// Released under the GNU General Public License, version 3
#include "mbed.h"


Serial rpi(USBTX, USBRX); // tx, rx


// Omron D6T-44L-06 (4x4) sensors. [1]_
//
// References:
//   .. [1] Omron, D6T-44L / D6T-8L Application note.
//          http://www.omron.com/ecb/products/sensor/special/mems/pdf/AN-D6T-01EN_r2.pdf
I2C thermo_sensors[2] = { I2C(p9, p10),     // Left sensor
                          I2C(p28, p27) };  // Right sensor

// Fis SB-AQ6B CO2 and Tobacco sensor. [2]_
//
// The sensor can read up to 3000 ppm.
//
// Notes:
//   Concentration of carbon dioxide in outside air is typically around
//   396 ppm, while exhaled air can go up to 13200 ppm. This sensor can only
//   read up to 3000 ppm.
// 
// References:
//   .. [2] Fis SB-AQ6B CO2 Monitoring Module Datasheet.
//          http://www.fisinc.co.jp/common/pdf/A051020-AQ6.pdf
AnalogIn co2(p17);

double temperatures[2][16] = {0};       // 16 temperatures for each sensor.
double past_temperatures[2][16] = {0};  // 16 temperatures for each sensor.


// Return the measured CO2 value.
float GetCO2() {
    return co2.read() * 5000 + 400;  // ppm
}


// Update the temperatures.
//
// The temperatures are stored in two global variables, `temperatures` and
// `past_temperatures`. If the temperature returned by a thermo sensor is
// outside the allowable range (defined as 5 to 50 degrees), reuse data
// from the previous read.
//
// The two arrays are updated by reference.
void UpdateTemperatures() {
  uint8_t thermo_address = 0x14;
  uint8_t thermo_start_read = 0x4c;
  
  char raw_data[35];
  short raw_temps[16];
  
  int itemp;
  
  for (int sensor_number = 0; sensor_number < 2; sensor_number++) {
    thermo_sensors[sensor_number].start();
    thermo_sensors[sensor_number].write(thermo_address);
    thermo_sensors[sensor_number].write(thermo_start_read);
    thermo_sensors[sensor_number].read(thermo_address, raw_data, 35);
  
    for (int i = 0; i < 17; i++) {
      itemp = (raw_data[2*i] & 0xff);
      itemp += raw_data[2*i + 1] * 256;
      if (i > 0) {
        raw_temps[i-1] = itemp;
      }
    }
  
    for (int i = 0; i < 16; i++) {
      if (raw_temps[i] > 50 && raw_temps[i] < 500) {  // 5 to 50 degrees
        temperatures[sensor_number][i] = 0.1 * raw_temps[i];
        past_temperatures[sensor_number][i] = temperatures[sensor_number][i];
      } else {
        temperatures[sensor_number][i] = past_temperatures[sensor_number][i];
      }
    }
  }
}


int main() {
  float co2_data;
  char packet;

  rpi.baud(38400);  // Match this in the RPi settings.

  while (1) {
    if (rpi.readable()) {
      packet = rpi.getc();

      if (packet == 7) {      // 7 is a request for identification.
	rpi.printf("arm\n");  // mbed name.
	continue;
      }
    }

    // Update data values.
    UpdateTemperatures();
    co2_data=GetCO2();

    // Send thermo data.
    for (int i=0; i < 2; i++) {
      for (int j=0; j < 16; j++) {
	rpi.printf("%4.1f ", temperatures[i][j]);
      }
    }
                
    // Send CO2 data and end line.
    rpi.printf("%4.1f\n", co2_data);
  }
}
