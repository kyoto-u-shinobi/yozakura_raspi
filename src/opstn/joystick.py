# (C) 2015  Kyoto University Mechatronics Laboratory
# Released under the GNU General Public License, version 3
import pygame
import sys


def interpret(dirs):
    """Interpret joystick axis position values to obtain a direction.

    The directions are Up, Down, Left, and Right, as well as their
    intermediates.

    Args:
        dirs: A tuple (x, y) containing the positions to be interpreted.
            Up and Right are normally positive.

    Returns:
        direction: "U", "D", "L", "R" if the motion is completely in a cardinal
            direction, or a combination of two directions if motion is in an
            ordinal direction. In those cases, the first letter would be "U" or
            "D", and the second letter would be "L" or "R". If there is no
            motion detected, return "none".
    """

    if dirs[1] > 0:
        vert = "U"
    elif dirs[1] < 0:
        vert = "D"
    else:
        vert = ""

    if dirs[0] > 0:
        hrz = "R"
    elif dirs[0] < 0:
        hrz = "L"
    else:
        hrz = ""

    if vert == "" and hrz == "":
        direction = "none"
    else:
        direction = vert + hrz

    return direction
    

def read_joystick(stick):
    """Read the state of all the inputs of a given joystick.

    Args:
        stick: The controller that needs to be checked. Should be a pygame
            joystick object.

    Returns:
        pressed: The buttons that are pressed. This is a list containing a
            human-readable representation of all the buttons pressed on the
            controller.
        dpad: A tuple containing the dpad position. The position is either -1,
            0, or 1.
        lstick: A tuple containing the positions for the left analog stick.
            Ranges between -1 and 1.
        rstick: A tuple containing the positions for the right analog stick.
            Ranges between -1 and 1.
    """
    button_list = ["□", "×", "○", "△",  # 0-3
                   "L1", "R1", "L2", "R2",  # 4-7
                   "select", "start",  # 8-9
                   "L3", "R3"]  # 10-11

    pygame.event.pump()  # Synchronize pygame with computer (i.e. Refresh)

    pressed = [button_list[i] for i in range(stick.get_numbuttons())
               if stick.get_button(i) != 0]
    dpad = stick.get_hat(0)
    lstick = (stick.get_axis(0), -stick.get_axis(1))
    rstick = (stick.get_axis(2), -stick.get_axis(3))

    return pressed, dpad, lstick, rstick

if __name__ == "__main__":
    pygame.init()
    stick = pygame.joystick.Joystick(0)
    stick.init()

    while True:
        try:
            pressed, dpad, lstick, rstick = read_joystick(stick)
            sys.stdout.write("dpad: {:4}  \
                              lstick: [{:5.2f}, {:5.2f}]  \
                              rstick: [{:5.2f}, {:5.2f}]  \
                              {:75}\r".format(interpret(dpad),
                                              lstick[0], lstick[1],
                                              rstick[0], rstick[1],
                                              str(pressed)))
            sys.stdout.flush()
        except KeyboardInterrupt:
            stick.quit()
            pygame.quit()
            print()
            print("Exiting!")
            break
