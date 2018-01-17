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

** Message formats *********************
Incoming requests from clients should be 4-character strings representing the
requested volume number (zero padding to make 4-characters). E.g. '0001'

Responses from the server will be JSON strings:
    If the results from the requested volume exist:
        e.g. {'foundResults': True, 'average':2432}
    If they don't:
        {'foundResults': False}
At a minimum, the response will contain the 'foundResults' entry. If foundResults
is true, the remaining entries are all of the key:value pairs that were output during
the analysis stage for this volume


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
        self.results = {}       # store results in dict like {'vol#':{results}}
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

        # atexit function, shut down server
        atexit.register(self.killServer)


    def run(self):
        """
        Run server, listening for requests and returning responses to clients
        """
        while self.alive:
            ### Listen for new connections, redirect clients to new socket
            connection, address = self.resultsSocket.accept()
            self.logger.debug('Results server received connection from: {}'.format(address))

            ### Get the requested volume (should be a 4-char string representing
            # volume number, e.g. '0001')
            recvMsg = connection.recv(4).decode()
            self.logger.debug('Received request: {}'.format(recvMsg))

            # reformat the requested volume to remove any leading 0s
            requestedVol = str(int(recvMsg))

            ### Look up the results for the requested volume
            volResults = self.requestLookup(requestedVol)

            ### Send the results to the client
            self.sendResults(connection, volResults)

            # close client connection
            connection.close()


    def updateResults(self, vol, volResults):
        """
        Add the supplied result to the results dictionary.
            - vol: the volume number associated with this result
            - volResults: dictionary containing all of the results for this volume
        """
        self.results[str(vol)] = volResults
        self.logger.debug('vol {} - {} added to resultsServer'.format(vol, volResults))


    def requestLookup(self, vol):
        """
        Check to see if there are results for the requested volume. Will return a
        dictionary of results for this volume. At a minimum, the dictionary will
        contain an entry with the key 'foundResults' and the value is True or
        False based on whether there are any results for this volume.
        """
        if str(vol) in self.results.keys():
            theseResults = self.results[str(vol)]
            theseResults['foundResults'] = True
        else:
            theseResults = {'foundResults': False}
        return theseResults


    def sendResults(self, connection, results):
        """
        Format the results dict to a json string, and send results to the client.
        Message will be sent in 2 waves: first a header indicating the msg length,
        and then the message itself
        """
        # format as json string and then convert to bytes
        formattedMsg = json.dumps(results).encode()

        # build then send header with info about msg length
        hdr = '{:d}\n'.format(len(formattedMsg))
        connection.send(hdr.encode())

        # send results as formatted message
        connection.sendall(formattedMsg)
        self.logger.debug('Sent result: {}'.format(formattedMsg))


    def killServer(self):
        self.alive = False



if __name__ == '__main__':
    port = 5556

    resultsServer = ResultsServer(port=port)
    #resultsServer.daemon = True
    resultsServer.start()
    print('Results Server alive and listening...')
