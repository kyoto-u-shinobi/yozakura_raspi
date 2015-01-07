import logging
import socketserver

class Handler(socketserver.BaseRequestHandler):
    def __init__(self, request, client_address, server):
        self.logger = logging.getLogger("{}_handler".format(client_address[0]))
        self.logger.debug("New handler created")
        super().__init__(request, client_address, server)

class Server(socketserver.ForkingMixIn, socketserver.TCPServer):
    def __init__(self, server_address, handler_class):
        self.logger = logging.getLogger("{}_server".format(server_address[0]))
        self.logger.debug("Creating server")
        super().__init__(server_address, handler_class)
        self.allow_reuse_address = True
        self.logger.info("Listening to port {}".format(server_address[1]))
