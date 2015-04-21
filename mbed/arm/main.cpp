#include <algorithm>
#include <iterator>
#include <vector>
#include "mbed.h"
#include "Dynamixel.h"
#include "MEMS.h"

struct ArmPacketBits {
                      unsigned int mode : 2;
                      unsigned int linear : 2;
                      unsigned int pitch : 2;
                      unsigned int yaw : 2;
                     };

union ArmPacket {
                 struct ArmPacketBits b;
                 unsigned char as_byte;
                };

Serial rpi(USBTX, USBRX);

AnalogIn co2(p20);

DigitalOut led_dx_read(LED1);
DigitalOut led_dx_move(LED2);
DigitalOut led_data_output(LED3);
DigitalOut led_done(LED4);

DigitalOut dx_low(p16);
DigitalOut dx_relay(p18);

AX12 linear(p13, p14, 0);
MX28 pitch(p13, p14, 1);
MX28 yaw(p13, p14, 2);

std::vector<Dynamixel*> servos = {linear, pitch, yaw};

MEMS thermo_sensors[2] = { MEMS(p9, p10),
                           MEMS(p28, p27) };

int goals[3];
int minima[3] = {100, 172, 360};
int maxima[3] = {720, 334, 360};
int speeds[3] = {0.1, 0.2, 0.2};
int inits[3] = {maxima[0], maxima[1], 0};
std::copy(std::begin(inits), std::end(inits), std::begin(goals));

void DxInitialize() {
  dx_low = 0;
  dx_relay = 1;
  
  for (int i=0; i < 3; i++) {
    servos[i].SetCWLimit(minima[i]);
    servos[i].SetCCWLimit(maxima[i]);
    servos[i].SetCRSpeed(speeds[i]);
  }

  linear.SetTorqueLimit(1);

  DxGoHome();
}

void DxGoHome() {
  linear.SetGoal(inits[0]);
  if (not linear.isMoving()) {
    pitch.SetGoal(inits[1]);
    yaw.SetGoal(inits[2]);
  }
}

void DxReset() {
  dx_relay = 0;
  wait_ms(10);
  dx_relay = 1;
}

void DxEnd() {
  led_done = 1;
  DxGoHome();
  dx_relay = 0;
}

float GetCO2() {
  return co2.read() * 5000 + 400;  // ppm
}

int main() {
  float positions[3];
  float values[3];
  float thermo_data[2][16];
  float co2_data;
  int commands[3];

  union ArmPacket packet;

  rpi.baud(38400);  // Match this in the RPi settings.

  DxInitialize();

  while (1) {
    if (rpi.readable()) {
      packet.as_byte = rpi.getc();
    }

    commands[0] = packet.linear;
    commands[1] = packet.pitch;
    commands[2] = packet.yaw;

    switch (packet.mode) {
      case 0: {
        led_dx_read = 1;
        for (int i=0; i < 3; i++) {
          positions[i] = servos[i].GetPosition();
	        if (i == 0) {
	          values[i] = servos[i].GetVolts();
	        } else {
	          values[i] = servos[i].GetCurrent();
	        }
        }
        led_dx_read = 0;

        led_dx_move = 1;
        for (int i=0; i < 3; i++) {
          if (commands[i] == 1) {
            goals[i]++;
          } else if (commands[i] == -1) {
            goals[i]--;
          }
          servos[i].SetGoal(goals[i]);
        }
        led_dx_move = 0;

	      for (int i=0; i < 2; i++) {
	        thermo_sensors[i].temp(thermo_data[i]);
	      }

	      co2_data = GetCO2();

	      led_data_output = 1;
	      // Send Dynamixel data
	      for (int i=0; i < 3; i++) {
	        rpi.printf("%4.1f %4.1f", positions[i], values[i]);
	      }

      	// Send thermo data
	      for (int i=0; i < 2; i++) {
	        for (int j=0; i < 16; i++) {
	          rpi.printf("%4.1f ", thermo_data[i][j]);
	        }
	      }

	      // Send CO2 data
	      rpi.printf("%4.1f", co2_data);

      	// End transmission
	      rpi.printf("\n");
	      led_data_output = 0;
        break;
      }
      
      case 1: {
        DxGoHome();
        break;
      } case 2: {
        DxReset();
        break;
      } case 3: {
	      led_done = 1;
        DxEnd();
        return 0;
      }
    }
  }
}
