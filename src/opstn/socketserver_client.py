import socket
import sys

host, port = ("localhost", 9000)
data = " ".join(sys.argv[1:])

sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

try:
    sock.connect((host, port))
    sock.sendall(bytes(data + "\n", "utf-8"))
    received = str(sock.recv(1024), "utf-8")

finally:
    sock.close()

print("Sent:     {}".format(data))
print("Received: {}".format(received))
