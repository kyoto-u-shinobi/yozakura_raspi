import pygame
import sys

def interpret(dirs):
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
    
def read_joystick():
    button_list = ["□", "×", "○", "△",  # 0-3
                   "L1", "R1", "L2", "R2",  # 4-7
                   "select", "start",  # 8-9
                   "L3", "R3"]  # 10-11

    pygame.event.pump()
    num_buttons = stick.get_numbuttons()

    pressed = [button_list[i] for i in range(num_buttons) if stick.get_button(i) != 0]
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
            pressed, dpad, lstick, rstick = read_joystick()
            sys.stdout.write("dpad: {:4}  lstick: [{:5.2f}, {:5.2f}]  rstick: [{:5.2f}, {:5.2f}]  {:75}\r".format(interpret(dpad), lstick[0], lstick[1], rstick[0], rstick[1], str(pressed)))
            sys.stdout.flush()
        except KeyboardInterrupt:
            stick.quit()
            pygame.quit()
            print()
            print("Exiting!")
            break
