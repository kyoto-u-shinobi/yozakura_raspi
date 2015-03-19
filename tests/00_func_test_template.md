# TEST_ID Functional Test Title

## Summary

* Test Type:            Is the test manual, scripted, or externally driven?
* Valid with Simulator: Is the test valid with the software running in simulation mode?
* Valid with Hardware:  Is the test valid with the software running on the actual hardware?
* Script Utilized:      If the test is automatic, what script is used?
* External C&C Source:  If the test utilizes an external command/control source, what is it?

## Objectives

This is where driving requirement (if available) is referenced as the reason for this test, and also where you describe what the dester should expect to see during and after the completion of the test. It does not define the pass/fail criteria.

## Pretest Setup

Define the required preteest actions here. These are the steps necessary in order to perform the test actions listed in the next section.

1. Procedure
2. Procedure
3. Procedure
4. *(additional items as necessary)*

## Test procedure

This is where the actual test procedure is defined. A procedure may consist of multiple steps. Each step should be a verifiable action (e.g. "Press R3 on the controller and verify that the server indicates that Reverse mode was toggled" or "Start the test script and verify that no error messages appear during script startup").

1. Step description
2. Step description
3. Step description
4. Step description
5. *(additional items as necessary)*

## Pass/Fail

This section defines the pass/fail criteria for this test. A test that passes would exhibit the behaviour defined by the driving requirement (if available) without exceeding nominal ranges or limits, or generating any erros during the execution of the test. A test failure might be a value that is too high or too low, or a function taking too long to execute. Any error that occured during the test that resulted in an error message is an obvious failure.
