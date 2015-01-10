# (C) 2015  Kyoto University Mechatronics Laboratory
# Released under the GNU General Public License, version 3
import pygame
import logging
from collections import namedtuple


class Position(object):
    """A class representing a joystick axis position.

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

    def __repr__(self):
        return str((self.x, self.y))

    def __str__(self):
        return "[{:5.2f}, {:5.2f}]".format(self.x, self.y)
    

class Buttons(object):
    """A class representing the button configuration of a joystick.

    Attributes:
        buttons: A list containing the state of each button.
    """
    _button_list = ("□", "×", "○", "△",  # 0-3
                "L1", "R1", "L2", "R2", # 4-7
                "select", "start",  # 8-9
                "L3", "R3", "PS")  # 10-12

    def __init__(self, buttons):
        """Inits the buttons.

        Args:
            buttons: A list containing the state of each button.
        """
        self.buttons = buttons

    def human(self):
        """A list of buttons which are pressed, in human-readable form."""
        return str([self._button_list[i] for i, button
                    in enumerate(self.buttons) if button])

    def __repr__(self):
        return str(self.buttons)

    def __str__(self):
        return str(self.buttons)


class State(object):
    """The state of the object.

    Attributes:
        dpad: The position of the dpad.
        lstick: The position of the left analog stick.
        rstick: The position of the right analog stick.
        buttons: The state of the buttons.
    """
    def __init__(self, dpad, lstick, rstick, buttons):
        """Inits the state.

        Args:
            dpad: The position of the dpad.
            lstick: The position of the left analog stick.
            rstick: The position of the right analog stick.
            buttons: The state of the buttons.
        """
        self.dpad = dpad
        self.lstick = lstick
        self.rstick = rstick
        self.buttons = buttons

    def human(self):
        """A human-readable representation of the state.

        To print on a single line, ensure that the terminal is at least 144
        characters wide.
        """
        out_1 = "dpad: {:4}".format(self.dpad.direction)
        out_2 = "lstick: {}".format(self.lstick)
        out_3 = "rstick: {}".format(self.rstick)
        out_4 = "buttons: {:75}".format(self.buttons.human())
        return "{}  {}  {}  {}".format(out_1, out_2, out_3, out_4)

    @property
    def data(self):
        """Return the raw data."""
        return self.dpad, self.lstick, self.rstick, self.buttons

    def __repr__(self):
        return str(self.data)

    def __str__(self):
        out_1 = "dpad: {:4}".format(self.dpad.direction)
        out_2 = "lstick: {}".format(self.lstick)
        out_3 = "rstick: {}".format(self.rstick)
        out_4 = "buttons: {:38}".format(str(self.buttons))
        return "{}  {}  {}  {}".format(out_1, out_2, out_3, out_4)


class Controller(object):
    """A controller to control the robot.

    Attributes:
        controller: The controller itself. (A pygame Joystick object.)
        stick_id: The ID of the controller.
        name: The name of the controller.
        controllers: A class variable containing all registered controllers.
    """
    pygame.init()
    controllers = {}

    def __init__(self, stick_id, name=None):
        """Inits a controller.

        Args:
            stick_id: The ID of the controller.
            name: (optional) The name of the controller.
        """
        self.logger = logging.getLogger("controller-{}".format(stick_id))
        self.logger.debug("Initializing controller")
        self.controller = pygame.joystick.Joystick(stick_id)
        self.stick_id = stick_id
        Controller.controllers[self] = stick_id

        if name is not None:
            self.name = name
        else:
            self.name = self.controller.get_name()
        self.controller.init()
        self.logger.info("Controller initialized")

    def get_state(self):
        """Read the state of all the inputs of the controller.

        Note that this is only tested with the Logitech RumblePad 2. Other
        input devices may have different configurations.

        Returns:
            The joystick state.
        """
        stick = self.controller
        n_buttons = stick.get_numbuttons()

        self.logger.debug("Syncronizing pygame")
        pygame.event.pump()

        self.logger.debug("Getting state")
        dpad = Position(*stick.get_hat(0))
        lstick = Position(stick.get_axis(0), stick.get_axis(1), inverted=True)
        rstick = Position(stick.get_axis(2), stick.get_axis(3), inverted=True)
        buttons = Buttons([stick.get_button(i) for i in range(n_buttons)])

        return State(dpad, lstick, rstick, buttons)
    
    def quit(self):
        """Safely quits a controller."""
        self.logger.info("Closing controller handler")
        self.controller.quit()
        del Controller.controllers[self]
        if not Controller.controllers:
            pygame.quit()

    @classmethod
    def quit_all(self):
        """A class method. Safely quits all controllers."""
        logging.info("Closing all controller handlers")
        for controller in list(Controller.controllers.keys()):
            controller.quit()

    def __repr__(self):
        return "{} (ID# {})".format(self.name, self.stick_id())

    def __str__(self):
        return self.name


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    stick_body = Controller(0, "Body controller")

    while True:
        try:
            print(stick_body.get_state().human(), end="\r")
        except KeyboardInterrupt:  # Exit safely.
            logging.info("")
            logging.info("Exiting")
            Controller.quit_all()
            break
