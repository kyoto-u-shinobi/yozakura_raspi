# (C) 2015  Kyoto University Mechatronics Laboratory
# Released under the GNU General Public License, version 3
import socket
import pickle

if __name__ == "__main__":
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect(("localhost", 9000))
    data = "body"
    while True:
        try:
            s.sendall(data.encode())
            result = s.recv(1024)
            dpad, lstick, rstick, buttons = pickle.loads(result)
            print(dpad, lstick, rstick, buttons, end="\r")
        except KeyboardInterrupt:
            break
    s.close()
