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
import socket
from threading import Thread

import numpy as np
import zmq

class ResultsServer(Thread):
    """
    Class to serve results from real-time analysis. This server will accept
    connections from remote clients, check if the requested results are available,
    and return a JSON-formatted message

    Input a dictionary called 'settings' that has (at least) the following keys:
        pynealHost: IP address of machine running Pyneal
        resultsServerPort: port # for results server socket [e.g. 5555]
    """

    def __init__(self, settings):
        # start the thread upon creation
        Thread.__init__(self)

        # set up logger
        self.logger = logging.getLogger('PynealLog')

        # configuration parameters
        self.alive = True
        self.results = {}       # store results in dict like {'vol#':{results}}
        self.host = settings['pynealHost']
        self.resultsServerPort = settings['resultsServerPort']
        self.maxClients = 5

        # launch server
        self.resultsSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.resultsSocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.resultsSocket.bind((self.host, self.resultsServerPort))
        self.resultsSocket.listen(self.maxClients)
        self.logger.debug('Results Server bound to {}:{}'.format(self.host, self.resultsServerPort))
        self.logger.info('Results Server alive and listening....')

        # atexit function, shut down server
        atexit.register(self.killServer)

        # set up socket to communicate with dashboard (if specified)
        if settings['launchDashboard']:
            self.dashboard = True
            context = zmq.Context.instance()
            self.dashboardSocket = context.socket(zmq.REQ)
            self.dashboardSocket.connect('tcp://127.0.0.1:{}'.format(settings['dashboardPort']))


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
            self.sendToDashboard(msgType='request', msg=recvMsg)

            # reformat the requested volume to remove any leading 0s
            requestedVol = str(int(recvMsg))

            ### Look up the results for the requested volume
            volResults = self.requestLookup(requestedVol)

            ### Send the results to the client
            self.sendResults(connection, volResults)
            self.logger.debug('Response: {}'.format(volResults))
            self.sendToDashboard(msgType='response', msg=volResults)

            # close client connection
            connection.close()


    def updateResults(self, volIdx, volResults):
        """
        Add the supplied result to the results dictionary.
            - vol: the volume number associated with this result
            - volResults: dictionary containing all of the results for this volume
        """
        self.results[str(volIdx)] = volResults
        self.logger.debug('vol {} - {} added to resultsServer'.format(volIdx, volResults))


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


    def sendToDashboard(self, msgType=None, msg=None):
        """
        If dashboard is launched, send the msg to the dashboard. The dashboard
        expects messages formatted in specific way, namely a dictionary with 2
        keys: 'topic', and 'content'

        Any message from the scanReceiver should set the topic as
        'resultsServerLog'.

        Content should be it's own dictionary with keys for 'type' and 'logString'
            - if msgType = 'request', include a key for logString that contains the
                requested volIdx
            - if msgType = 'respone', include key for logString that contains the
                json response from the server, AND a key for success indicating
                whether or not the results were found for the requested volume
        """
        if self.dashboard:
            topic = 'resultsServerLog'
            if msgType == 'request':
                content = {'type': msgType,
                            'logString': msg}
            elif msgType == 'response':
                content = {'type': msgType,
                            'logString': json.dumps(msg),
                            'success': msg['foundResults']}

            # format messsage
            dashboardMsg = {'topic': topic,
                            'content': content}

            # send msg to dashboard
            self.dashboardSocket.send_json(dashboardMsg)
            response = self.dashboardSocket.recv_string()

    def killServer(self):
        self.alive = False


if __name__ == '__main__':
    # set up settings dict
    settings = {'resultsServerPort': 5556}

    resultsServer = ResultsServer(settings)
    #resultsServer.daemon = True
    resultsServer.start()
    print('Results Server alive and listening...')
