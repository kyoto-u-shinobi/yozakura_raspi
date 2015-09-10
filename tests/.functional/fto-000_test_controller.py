import logging
import sys

from opstn import Controller


def main():
    stick = Controller(0, "Test controller")

    while True:
        print(stick.get_state(), end="\r")


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)

    try:
        main()
    except KeyboardInterrupt:
        print()
        Controller.shutdown_all()
        sys.exit(0)
