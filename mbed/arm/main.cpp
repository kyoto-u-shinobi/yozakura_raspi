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

DigitalOut dx_low(p16);
DigitalOut dx_relay(p18);

std::vector<Dynamixel*> servos;
AX12 *linear = new AX12(p13, p14, 0);
MX28 *pitch = new MX28(p13, p14, 1);
MX28 *yaw = new MX28(p13, p14, 2);

MEMS thermo_sensors[] = { MEMS(p9, p10),
                          MEMS(p28, p27) };

int minima[] = {100, 172, 360};
int maxima[] = {300, 334, 360};
float speeds[] = {0.1, 0.2, 0.2};
int inits[] = {maxima[0], maxima[1], 0};
int goals[] = {maxima[0], maxima[1], 0};

void DxGoHome() {
  linear->SetGoal(inits[0]);
  if (not linear->isMoving()) {
    pitch->SetGoal(inits[1]);
    yaw->SetGoal(inits[2]);
  }
}

void DxInitialize() {
  dx_low = 0;
  dx_relay = 1;
  
  for (int i=0; i < 3; i++) {
    servos[i]->SetCWLimit(minima[i]);
    servos[i]->SetCCWLimit(maxima[i]);
    servos[i]->SetCRSpeed(speeds[i]);
  }
}

void DxReset() {
  dx_relay = 0;
  wait_ms(10);
  DxInitialize();
}

void DxEnd() {
  DxGoHome();
  while (lineaer->isMoving()) {}
  DxGoHome();
  while (pitch->isMoving() or yaw->isMoving()) {}
  dx_relay = 0;
}

float GetCO2() {
  return co2.read() * 5000 + 400;  // ppm
}

int main() {
  servos.push_back(linear);
  servos.push_back(pitch);
  servos.push_back(yaw);
  
  float positions[3];
  float values[3];
  float thermo_data[2][16];
  float co2_data;
  int commands[3];

  union ArmPacket packet;

  rpi.baud(38400);  // Match this in the RPi settings.

  DxInitialize();  // Comment this out when testing without the arm.
  DxGoHome();
  
  while (1) {
    packet.as_byte = rpi.getc();

    for (int i = 0; i < 3; i++) {
      positions[i] = -1;
      values[i] = -1;
    }

    commands[0] = packet.b.linear;
    commands[1] = packet.b.pitch;
    commands[2] = packet.b.yaw;
    
    switch (packet.b.mode) {
      case 0: {
        if (not dx_relay) {
          break;
        }
        for (int i=0; i < 3; i++) {
            positions[i] = servos[i]->GetPosition();
            goals[i] = positions[i];
            if (i == 0) {
              values[i] = servos[i]->GetVolts();
            } else {
              values[i] = servos[i]->GetCurrent();
            }
        }

        linear->SetTorqueLimit(1);  // Reset torque limit
        for (int i=0; i < 3; i++) {
          if (commands[i] == 1) {
            goals[i]++;
          } else if (commands[i] == 2) {
            goals[i]--;
          }
          servos[i]->SetGoal(goals[i]);
        }
        break;
      } case 1: {
        if (dx_relay) {
          DxGoHome();
        }
        break;
      } case 2: {
        DxReset();
        break;
      } case 3: {
        if (packet.b.linear) {
          rpi.printf("arm\n");
        } else {
          if (dx_relay) {
            DxEnd();
          }
        }
        break;
      }
    }
    for (int i=0; i < 2; i++) {
      thermo_sensors[i].temp(thermo_data[i]);
    }
    
    co2_data = GetCO2();
    
    // Send Dynamixel position
    for (int i=0; i < 3; i++) {
      rpi.printf("%4.1f ", positions[i]);
    }
    
    // Send Dynamixel values
    for (int i=0; i < 3; i++) {
      rpi.printf("%4.1f ", values[i]);
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
  }
}
