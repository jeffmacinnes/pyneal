
from threading import Thread
import zmq


class WebServer(Thread):
    """
    Class to represent the server that is receiving messages from different clients
    """

    def __init__(self, socket):
        Thread.__init__(self)

        self.socket = socket
        print('here!')
        self.alive = True

    def run(self):
        while self.alive:

            # listen for responses
            msg = self.socket.recv_string()
            print("webServer got message: {}".format(msg))

            # send reply
            self.socket.send_string('Got it')

    def kill(self):
        self.alive = False


def callThisFunction(socket):
    webServer = WebServer(socket)
