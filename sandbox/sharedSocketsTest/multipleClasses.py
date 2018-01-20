

import zmq
import os
import sys
from threading import Thread

import time



class TestModule(Thread):
    """
    Class to represent an example pyneal module. We'll make multiple instances of
    this module, and see if we can pass in the same socket object. This is to test
    whether multiple classes can send different messages to the webserver using the
    same shared socket
    """

    def __init__(self, socket, name='className'):
        # start the Thread
        Thread.__init__(self)

        print('Launching webserver')

        # give this class a name
        self.name = name

        # get a local reference to the socket object
        self.socket = socket

        self.alive = True

    def run(self):
        # The class will send out a message with it's name and count to the socket
        # every second
        self.counter = 0
        while self.alive:

            # sent message
            msg = 'socket: {}, value: {}'.format(self.name, self.counter)
            self.socket.send_string(msg)

            # get replay
            serverResp = self.socket.recv_string()
            print('socket: {} got response from server: {}'.format(self.name, serverResp))

            # increment counter:
            self.counter += 1

            # pause
            time.sleep(1)

    def kill(self):
        self.alive = False



class WebServer(Thread):
    """
    Class to represent the server that is receiving messages from different clients
    """

    def __init__(self, socket):
        Thread.__init__(self)

        self.socket = socket

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


if __name__ == '__main__':

    port = 6666

    # set up webserver socket
    context = zmq.Context.instance()
    webServerSocket = context.socket(zmq.PAIR)
    webServerSocket.bind('tcp://127.0.0.1:{}'.format(port))
    print('webserver alive and listening')

    # set up socket for clients to use
    clientSocket = context.socket(zmq.PAIR)
    clientSocket.connect('tcp://127.0.0.1:{}'.format(port))


    # Launch instances of classes
    webServer = WebServer(webServerSocket)
    webServer.daemon = True
    webServer.start()

    jeffModule = TestModule(clientSocket, name='jeffModule')
    jeffModule.daemon = False
    jeffModule.start()

    luukaModule = TestModule(clientSocket, name='luukaModule')
    luukaModule.daemon = False
    luukaModule.start()
