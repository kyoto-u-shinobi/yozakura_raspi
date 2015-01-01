# (C) 2015  Kyoto University Mechatronics Laboratory
# Released under the GNU General Public License, version 3
import multiprocessing as mp
import joystick
import socket
import logging
import pickle


class Server(object):
    """Server class to communicate via TCP.

    This class is capable of handling multiple clients simultaneously by
    creating a subprocess handler for each new client.

    Attributes:
        hostname: The hostname or IP Address of the server.
        port: The port used for communication.
        socket: The socket opened by the server.
    """
    def __init__(self, hostname, port):
        """Inits the server.

        Args:
            hostname: The hostname or IP Address of the server.
            port: The port used for communication.
        """
        self.logger = logging.getLogger("server")
        self.hostname = hostname
        self.port = port

    def start(self):
        """Starts the server."""
        self.logger.debug("Starting server")
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.bind((self.hostname, self.port))
        self.socket.listen(1)
        self.logger.info("Server started")
        
        while True:
            """Fork a new process to deal with a new client."""
            conn, address = self.socket.accept()
            self.logger.debug("Got connection")
            process = mp.Process(target=self.handle, args=(conn, address))
            process.daemon = True
            process.start()
            self.logger.debug("Started process {}".format(process))

    def handle(self, connection, address):
        """A client handler. A new one is started for each client.
        
        Args:
            connection: The socket object to be used for communication.
            address: The address of the socket object.
        """
        logger = logging.getLogger("process-{}".format(address[1]))
        try:
            logger.info("Connected to {}".format(address[0]))
            while True:
                data_raw = connection.recv(1024)
                data = data_raw.decode("utf-8")
                logger.debug('Received data: "{}"'.format(data))
                if data == "":
                    logger.debug("Socket closed remotely")
                    break
                elif data == "body":
                    logger.debug("Client requesting body controller input")
                    state = stick_body.get_state()
                    reply = pickle.dumps(state.data)
                try:
                    connection.sendall(str.encode(reply))
                except TypeError:  # Already bytecode
                    connection.sendall(reply)
                logger.debug("Sent reply")
        except KeyboardInterrupt:
            logger.debug("Keyboard interrupt received")
        finally:
            logger.info("Closing socket")
            connection.close()

    def quit(self):
        """Quits the server and kills all subprocesses."""
        for process in mp.active_children():
            logging.info("Shutting down process {}".format(process))
            process.terminate()
            process.join()


if __name__=="__main__":
    logging.basicConfig(level=logging.INFO)
    stick_body = joystick.Controller(0)

    server = Server("localhost", 9000)
    try:
        server.start()
    except KeyboardInterrupt:
        logging.debug("Keyboard interrupt received")
        pass
    finally:
        logging.info("Shutting down...")
        logging.info("Closing joystick handlers")
        joystick.Controller.quit_all()
        server.quit()
    logging.info("All done")
