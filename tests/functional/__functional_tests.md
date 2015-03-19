# Functional Tests

These tests should be executed periodically when unit tests pass to ensure that the functional requirements are met.

## FT-000 Test the mbed connected to the Raspberry Pi

### Summary

* **Test Type:**            Manual
* **Valid with Simulator:** No
* **Valid with Hardware:**  Yes
* **Script Utilized:**      ft-000_test_rpi_mbed.py
* **External C&C Source:**  None

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
10. In the test script, define `motor` as one of the four motors that have been predefined, depending on the pins the motor has been connected to.

### Test procedure

This is where the actual test procedure is defined. A procedure may consist of multiple steps. Each step should be a verifiable action (e.g. "Press R3 on the controller and verify that the server indicates that Reverse mode was toggled" or "Start the test script and verify that no error messages appear during script startup").

1. Step description
2. Step description
3. Step description
4. Step description
5. *(additional items as necessary)*

### Pass/Fail

This section defines the pass/fail criteria for this test. A test that passes would exhibit the behaviour defined by the driving requirement (if available) without exceeding nominal ranges or limits, or generating any erros during the execution of the test. A test failure might be a value that is too high or too low, or a function taking too long to execute. Any error that occured during the test that resulted in an error message is an obvious failure.
