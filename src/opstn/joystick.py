# (C) 2015  Kyoto University Mechatronics Laboratory
# Released under the GNU General Public License, version 3
import pygame
from collections import namedtuple


class Position(object):
    """A class representing the joystick axis position.

    Attributes:
            x: The x-position of the axis.
            y: The y-position of the axis.
            inverted: Whether the direction is y-inverted.
    """
    def __init__(self, x, y, inverted=False):
        """Inits position.

        Args:
            x: The x-position of the axis.
            y: The y-position of the axis.
            inverted: (optional) Whether the direction is y-inverted. Default
                is False.
        """
        self.x = x
        self.y = y
        self.inverted = inverted

    @property
    def direction(self):
        """Determine the direction represented by the joystick axis position.

        The directions are Up, Down, Left, and Right, and their intermediates.

        Returns:
            "U", "D", "L", "R" if the motion is completely in a cardinal
                direction, or a combination of two directions if motion is in
                an ordinal direction. In those cases, the first letter would be
                "U" or "D", and the second letter would be "L" or "R". If there
                is no motion detected, return "none".
        """
        if self.y > 0:
            vert = "D" if self.inverted else "U"
        elif self.y < 0:
            vert = "U" if self.inverted else "D"
        else:
            vert = ""

        if self.x > 0:
            hrz = "R"
        elif self.x < 0:
            hrz = "L"
        else:
            hrz = ""

        if vert == "" and hrz == "":
            direction = "none"
        else:
            direction = vert + hrz

        return direction
    

def read_joystick(stick):
    """Read the state of all the inputs of a given joystick or controller.

    Note that this is only tested with the Logitech RumblePad 2. Other input
    devices may have different configurations.

    Args:
        stick: The joystick that needs to be checked. Should be a pygame
            joystick object.

    Returns:
        A named tuple containing:
            buttons: A list containing a human-readable representation of all
                the currently-depressed buttons on the controller.
            dpad: The dpad position. Can contain either -1, 0, or 1.
            lstick: The left analog stick position. Ranges from -1 to 1.
            rstick: The right analog stick position. Ranges from -1 to 1.
    """
    State = namedtuple("State", ["buttons", "dpad", "lstick", "rstick"])
    buttons = ("□", "×", "○", "△",  # 0-3
               "L1", "R1", "L2", "R2", # 4-7
               "select", "start",  # 8-9
               "L3", "R3")  # 10-11
    n_buttons = stick.get_numbuttons()

    pygame.event.pump()  # Synchronize pygame with computer (i.e. Refresh)

    pressed = [buttons[i] for i in range(n_buttons) if stick.get_button(i) > 0]
    dpad = Position(*stick.get_hat(0))  # Unpack the tuple.
    lstick = Position(stick.get_axis(0), stick.get_axis(1), inverted=True)
    rstick = Position(stick.get_axis(2), stick.get_axis(3), inverted=True)

    state = State(pressed, dpad, lstick, rstick)
    return state


if __name__ == "__main__":
    pygame.init()
    stick = pygame.joystick.Joystick(0)  # First controller
    stick.init()

    while True:
        try:
            pressed, dpad, lstick, rstick = read_joystick(stick)
            out_1 = "dpad: {:4}".format(dpad.direction)
            out_2 = "lstick: [{:5.2f}, {:5.2f}]".format(lstick.x, lstick.y)
            out_3 = "rstick: [{:5.2f}, {:5.2f}]".format(rstick.x, rstick.y)
            out_4 = "buttons: {:75}".format(str(pressed))
            output = "{}  {}  {}  {}".format(out_1, out_2, out_3, out_4)
            print(output, end="\r")
        except KeyboardInterrupt:  # Exit safely.
            stick.quit()
            pygame.quit()
            print()
            print("Exiting!")
            break
