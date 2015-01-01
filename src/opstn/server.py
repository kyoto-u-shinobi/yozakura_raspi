# (C) 2015  Kyoto University Mechatronics Laboratory
# Released under the GNU General Public License, version 3
import multiprocessing as mp
import joystick
import socket
import logging
import pickle


class Server(object):
    def __init__(self, hostname, port):
        self.logger = logging.getLogger("server")
        self.hostname = hostname
        self.port = port

    def start(self):
        self.logger.debug("Listening...")
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.bind((self.hostname, self.port))
        self.socket.listen(1)
        
        while True:
            conn, address = self.socket.accept()
            self.logger.debug("Got connection")
            process = mp.Process(target=self.handle, args=(conn, address))
            process.daemon = True
            process.start()
            self.logger.debug("Started process {}".format(process))

    def handle(self, connection, address):
        logger = logging.getLogger("process-{}".format(address[1]))
        try:
            logger.debug("Connected to {}".format(address[0]))
            while True:
                data_raw = connection.recv(1024)
                data = data_raw.decode("utf-8")
                if data == "":
                    logger.debug("Socket closed remotely")
                    break
                elif data == "body":
                    logger.debug("Getting body controller data")
                    state = stick_body.get_state()
                    reply = pickle.dumps(state.data)
                else:
                    reply = "Did not understand '{}'".format(data)
                logger.debug("Received data '{}'".format(data))
                try:
                    connection.sendall(str.encode(reply))
                except TypeError:
                    connection.sendall(reply)
                logger.debug("Sent reply")
        except KeyboardInterrupt:
            logger.exception("Keyboard interrupt")
        finally:
            logger.debug("Closing socket")
            connection.close()


if __name__=="__main__":
    logging.basicConfig(level=logging.ERROR)
    stick_body = joystick.Controller(0)

    server = Server("localhost", 9000)
    try:
        logging.info("Starting server...")
        server.start()
    except KeyboardInterrupt:
        logging.info("Keyboard interrupt received!")
    finally:
        logging.info("Shutting down...")
        logging.info("Quitting joystick {}".format(stick_body.stick_id))
        stick_body.quit()
        for process in mp.active_children():
            logging.info("Shutting down process {}".format(process))
            process.terminate()
            process.join()
    logging.info("All done")
