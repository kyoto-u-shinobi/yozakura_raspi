# Functional Tests

These tests should be executed periodically when unit tests pass to ensure that the functional requirements are met.

## FTR-000 Test the mbed connected to the Raspberry Pi

### Summary

| Item                 | Value                |
| :------------------- | :------------------- |
| Test Type            | Manual               |
| Valid with Simulator | No                   |
| Valid with Hardware  | Yes                  |
| Script utilized      | ftr-000_test_mbed.py |
| External C&C Source  | None                 |

### Objectives

This test tests that the mbed connected to the Raspberry Pi can correctly drive a single motor based on given speed inputs selected by the tester. As different speeds are selected, the speed and/or direction of the motor should change appropriately.

### Pretest Setup

Before beginning the test, follow this procedure:

1. Connect the motor to the motor driver OUTA and OUTB pins.
2. Connect the motor driver's GND pin to the mbed's ground pin.
3. Connect the motor driver's PWM pin to the mbed's pin 21, 22, 23, or 24.
4. Connect the motor driver's DIR pin to the mbed's pin 11, 12, 13, or 14.
5. Connect the motor driver's FF1 pin to the pi's pin 11, 15, 31, or 35.
6. Connect the motor driver's FF1 pin to the pi's pin 12, 16, 32, or 36.
7. Connect the motor driver's RST pin to the pi's pin 13, 18, 33, or 37.
8. Connect the batteries to the motor driver's V+ and GND pins.
9. Connect the mbed to the Raspberry Pi via an A-to-MiniB USB cable.
10. In the test script, set the maximum speeds for the motors depending on which motor is connected, and the load on the motor.
11. In the test script, define `motor` as one of the four motors that have been predefined, depending on the pins the motor has been connected to.
12. Start the script by running it from the root folder using `sudo python3 -m tests.functional.ftr-000_test_mbed`

### Test procedure

1. Press "a" several times and verify that the motor turns in the positive direction. Ensure that the speed never goes above the defined maximum speed.
  * If the motor does not turn, it might mean that a short-circuit fault had occurred during startup. Press "r" or "R" to reset the motor driver and clear the fault.
  2. Press "z" several times and verify that the motor slows down before starting to turn in the negative direction. Ensure that the speed never goes above the defined maximum speed.
  3. Press "a" several times and verify that the motor slows down.
  4. Press "q" or "Q" and verify that the motor stops.
  5. Press "A" and verify that the motor turns at the defined maximum speed in the positive direction.
  6. Press "q" or "Q" and verify that the motor stops.
  7. Press "Z" and verify that the motor turns at the defined maximum speed in the negative direction.
  8. Press "q" or "Q" and verify that the motor stops.

### Pass/Fail

A pass occurs when all the steps of the test procedure produce the expeted results. A failure occurs when an unexpected behaviour is seen, or if a short-circuit fault is triggered.

