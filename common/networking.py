import logging
import socketserver

class HandlerBase(socketserver.BaseRequestHandler):
    def __init__(self, request, client_address, server):
        self.logger = logging.getLogger("{}_handler".format(client_address[0]))
        self.logger.debug("New handler created")
        super().__init__(request, client_address, server)


class ServerBase(socketserver.ForkingMixIn, socketserver.TCPServer):
    allow_reuse_address = True
    def __init__(self, server_address, handler_class):
        self.logger = logging.getLogger("{}_server".format(server_address[0]))
        self.logger.debug("Creating server")
        super().__init__(server_address, handler_class)
        self.logger.info("Listening to port {}".format(server_address[1]))
