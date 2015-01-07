import socketserver

class EchoHandler(socketserver.BaseRequestHandler):
    def handle(self):
        # Echo the back to the client
        self.data = self.request.recv(1024).strip()
        self.request.sendall(self.data.upper())

if __name__ == '__main__':
    host, port = ("localhost", 9000)
    server = socketserver.TCPServer((host, port), EchoHandler)
    server.serve_forever()
