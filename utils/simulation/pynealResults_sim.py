""" Tool to simulate the output results server of Pyneal.

This tool will simulate the results server from  Pyneal as well as populate it
with fake data at a rate of one new volume per TR (user can specify TR below)

Once running, the resultsServer will listen for requests over the specified
socket and return a response.

** Message formats *********************
Incoming requests from clients should be 4-character strings representing the
requested volume number (zero padding to make 4-characters). E.g. '0001'

Responses from the server will be JSON strings:
    If the results from the requested volume exist:
        e.g. {'foundResults': True, 'average':2432}
    If they don't:
        {'foundResults': False}

"""
import json
import atexit
import socket
from threading import Thread
import time
import argparse

import numpy as np


class ResultsServer(Thread):
    """ Class to serve results from real-time analysis.

    This server will accept connections from remote clients, check if the
    requested results are available, and return a JSON-formatted message

    """
    def __init__(self, settings):
        """ Initialize the class

        Parameters
        ----------
        settings : dict
            dictionary that has (at least) the following keys:
            -resultsServerPort: port # for results server socket [e.g. 5555]
        """
        # start the thread upon creation
        Thread.__init__(self)

        # configuration parameters
        self.alive = True
        self.results = {}       # store results in dict like {'vol#':{results}}
        self.host = settings['pynealHost']
        self.resultsServerPort = settings['resultsServerPort']
        self.maxClients = 1

        # launch server
        self.resultsSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.resultsSocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.resultsSocket.bind((self.host, self.resultsServerPort))
        self.resultsSocket.listen(self.maxClients)
        print('Results Server bound to {}:{}'.format(self.host, self.resultsServerPort))
        print('Results Server alive and listening....')

        # atexit function, shut down server
        atexit.register(self.killServer)

    def run(self):
        """ Run server, listening for requests and returning responses to
        clients

        """
        while self.alive:
            ### Listen for new connections, redirect clients to new socket
            try:
                connection, address = self.resultsSocket.accept()
                print('Results server received connection from: {}'.format(address))

                ### Get the requested volume (should be a 4-char string representing
                # volume number, e.g. '0001')
                recvMsg = connection.recv(4).decode()
                print('Received request: {}'.format(recvMsg))

                # reformat the requested volume to remove any leading 0s
                requestedVol = str(int(recvMsg))

                ### Look up the results for the requested volume
                volResults = self.requestLookup(requestedVol)

                ### Send the results to the client
                self.sendResults(connection, volResults)
                print('Response: {}'.format(volResults))

                # close client connection
                connection.close()
                
            except ConnectionAbortedError:
                print('Attemping to connect to a closed socket!')
                return

    def updateResults(self, volIdx, volResults):
        """ Add the supplied result to the results dictionary.

        There is a master dictionary (called `results`) that stores the
        analysis results for each volume throughout a scan. The keys in this
        master dictionary will be the volume indices; the values for each key
        will itself be a (nested) dictionary containing the specific result(s)
        for that volume.

        This function takes the results dictionary for a single volume, and
        adds it to the master dictionary under a new key (the volIdx).

        Parameters
        ----------
        volIdx : int
            volume index (0-based) of the current volume
        volResults : dict
            dictionary containing the result(s) of the analysis for the current
            volume

        """
        self.results[str(volIdx)] = volResults
        print('vol {} - {} added to resultsServer'.format(volIdx, volResults))

    def requestLookup(self, volIdx):
        """ Lookup results for the requested volume

        Check to see if there are results for the requested volume. Will
        return a dictionary of results for this volume. At a minimum, the
        dictionary will contain an entry with the key 'foundResults' and the
        value is True or False based on whether there are any results for this
        volume.

        Parameters
        ----------
        volIdx : int
            volume index (0-based) of the volume you are requesting results for

        Returns
        -------
        theseResults : dict
            dictionary containing the retrieved results for this volume. At a
            minimum, this dictionary will contain an entry with the key
            'foundResults' and the value is True or False based on whether
            there are any results for this volume. If True, the remaining
            items in the dictionary will reflect all of the stored results
            for the requested volume

        """
        if str(volIdx) in self.results.keys():
            theseResults = self.results[str(volIdx)]
            theseResults['foundResults'] = True
        else:
            theseResults = {'foundResults': False}
        return theseResults

    def sendResults(self, connection, results):
        """ Send the results back to the End User

        Format the results dict to a json string, and send results to the End
        User. Message will be sent in 2 waves: first a header indicating the
        msg length, and then the message itself.

        The size of results messages can vary substantially based on the
        specific analyses performed, and whether or not the the results were
        computed for the requested volume or not yet. Sending the message in
        this way allows the End User to know precisely how big the results
        message will be, and read from the socket accordingly.

        Parameters
        ----------
        connection : socket object
            socket object that is used for communicating with the End User
        results : dict
            dictionary containing the results to be sent to the End User

        """
        # format as json string and then convert to bytes
        formattedMsg = json.dumps(results).encode()

        # build then send header with info about msg length
        hdr = '{:d}\n'.format(len(formattedMsg))
        connection.send(hdr.encode())

        # send results as formatted message
        connection.sendall(formattedMsg)
        print('Sent result: {}'.format(formattedMsg))

    def killServer(self):
        """ Close the thread by setting the alive flag to False """
        self.alive = False
        self.resultsSocket.close()


def launchPynealSim(TR, host, resultsServerPort, keepAlive=False):
    """ Launch a Pyneal simulator

    This simulator will mimic Pyneal just enough to launch the simulated
    results server and populate it with fake data AS THOUGH a real scan was
    occuring.

    Start the results server going on its own thread where it will listen for
    incoming responses, and then send a response to each request.

    Meanwhile, start sending fake results to the resultsServer at a rate set
    by the TR

    Parameters :
    TR : int
        TR of fake scan, in ms
    host : string
        IP address of the results server
    resultsServerPort : int
        Port number for the results server to listen on
    keepAlive : bool, optional
        Flag for whether to shut the server down or not once all of the data
        has been added (default=False). For debugging purposes, it may be
        useful to keep the server alive so that you may continually send
        requests, even after the end of the simulated "scan". In that case,
        set this flag to True

    """
    # Results Server Thread, listens for requests from end-user (e.g. task
    # presentation), and sends back results
    settings = {'pynealHost': host, 'resultsServerPort': resultsServerPort}
    resultsServer = ResultsServer(settings)
    resultsServer.daemon = True
    resultsServer.start()
    print('Starting Results Server...')

    # Start making up fake results
    for volIdx in range(500):
        # generate a random value
        avgActivation = np.around(np.random.normal(loc=2400, scale=15), decimals=2)
        result = {'average': avgActivation}

        # send result to the resultsServer
        resultsServer.updateResults(volIdx, result)

        # pause for TR
        time.sleep(TR / 1000)

    if not keepAlive:
        print('Shutting down simulated Results Server')
        resultsServer.killServer()

if __name__ == '__main__':
    # parse arguments
    parser = argparse.ArgumentParser(description="Pyneal-Results Server Simulator",
                                     formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('-t', '--TR',
                        default=1000,
                        type=int,
                        help='TR (in ms)')
    parser.add_argument('-sh', '--sockethost',
                        default='127.0.0.1',
                        type=str,
                        help='Pyneal socket host')
    parser.add_argument('-sp', '--socketport',
                        default=5556,
                        type=int,
                        help='Pyneal socket port')
    parser.add_argument('--keepAlive',
                        default=False,
                        action='store_true')
    args = parser.parse_args()
    print(args.keepAlive)
    launchPynealSim(args.TR, args.sockethost, args.socketport, keepAlive=args.keepAlive)
