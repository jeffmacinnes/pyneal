"""
Class to serve the results of an on-going real-time analysis and make them
available upon request.

This tool is designed to run in a separate thread, where it will:
    - Listen for incoming requests from clients (e.g. experimental presentation
    software)
    - Check to see if the requested information is available
    - Return the requested information (or a message indicating it is not
    available yet)

Elsewhere, Pyneal uses the powerful Zmq socket library for network communication,
however in this case the results server needs to be able to talk to clients that
are connecting using 'normal' socket libraries that are incompatible with ZMQ.
Thus, the results server is a traditional TCP socket server.

Message format:
Incoming requests from clients should take the form: XXXXXX

Responses from the server will be JSON strings like:
    If the results from the requested volume exist:
        {'foundResults': True, 'data': [val1, val2, ... ] }
    If they don't:
        {'foundResults': False}



"""
# python 2/3 compatibility
from __future__ import print_function

import os
import sys
import logging
import json
import atexit
from threading import Thread

import numpy as np
import socket

class ResultsServer(Thread):
    """
    Class to serve results from real-time analysis. This server will accept
    connections from remote clients, check if the requested results are available,
    and return a JSON-formatted message
    """

    def __init__(self, host='127.0.0.1', port=5556):
        # start the thread upon creation
        Thread.__init__(self)

        # set up logger
        self.logger = logging.getLogger('PynealLog')

        # configuration parameters
        self.alive = True
        self.resultsDict = {}       # empty dictionary to store incoming results
        self.host = host
        self.port = port
        self.maxClients = 1

        # launch server
        self.resultsSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.resultsSocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.resultsSocket.bind((self.host, self.port))
        self.resultsSocket.listen(self.maxClients)
        self.logger.debug('Results Server bound to {}:{}'.format(self.host, self.port))
        self.logger.info('Results Server alive and listening....')

        # atexit function
        atexit.register(self.killServer)

    def run(self):
        while self.alive:
            # listen for new connections, redirect clients to new socket
            connection, address = self.resultsSocket.accept()
            print('client connected!')

            # get the request
            requestMsg = connection.recv(512).decode()      # receive message from client
            print(requestMsg)
            self.logger.debug('Received request: {}'.format(requestMsg))

            # look up request
            result = {'response':'no'}
            connection.send(json.dumps(result).encode())

            self.logger.debug('Sent result: {}'.format(result))

            # close client connection
            connection.close()

    def killServer(self):
        self.alive = False







if __name__ == '__main__':
    port = 5556

    resultsServer = ResultsServer(port=port)
    #resultsServer.daemon = True
    resultsServer.start()
    print('ere')
