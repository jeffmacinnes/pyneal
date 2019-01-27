""" Tools to serve the analysis results during an on-going real-time run and
make them available upon request.

This tool is designed to run in a separate thread, where it will:
    - Listen for incoming requests from clients (e.g. experimental presentation
    software)
    - Check to see if the requested information is available
    - Return the requested information (or a message indicating it is not
    available yet)

Elsewhere, Pyneal uses the powerful Zmq socket library for network
communication, however in this case the results server needs to be able to talk
to clients that are connecting using 'normal' socket libraries that are
incompatible with ZMQ. Thus, the results server is a traditional TCP socket
server.

** Message formats *********************
Incoming requests from clients should be 4-character strings representing the
requested volume number (zero padding to make 4-characters). E.g. '0001'

Responses from the server will be JSON strings:
    If the results from the requested volume exist:
        e.g. {'foundResults': True, 'average':2432}
    If they don't:
        {'foundResults': False}

At a minimum, the response will contain the 'foundResults' entry. If
foundResults is true, the remaining entries are all of the key:value pairs that
were output during the analysis stage for this volume

"""
from os.path import join
import logging
import json
import atexit
import socket
from threading import Thread

import zmq


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
            dictionary that contains all of the pyneal settings for the current
            session. This dictionary is loaded/configured by the GUI once
            Pyneal is first launched. At minumum, this dict must contain the
            following fields:
            - pynealHost: IP address of machine running Pyneal
            - resultsServerPort: port # for results server socket [e.g. 5555]

        """
        # start the thread upon creation
        Thread.__init__(self)

        # set up logger
        self.logger = logging.getLogger('PynealLog')

        # configuration parameters
        self.alive = True
        self.results = {}       # store results in dict like {'vol#':{results}}
        self.host = '0.0.0.0'   # make accessible to other computers on same network
        self.resultsServerPort = settings['resultsServerPort']
        self.maxClients = 5
        self.seriesOutputDir = settings['seriesOutputDir']

        # launch server
        self.resultsSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.resultsSocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.resultsSocket.bind((self.host, self.resultsServerPort))
        self.resultsSocket.listen(self.maxClients)
        self.logger.debug('bound to {}:{}'.format(self.host, self.resultsServerPort))
        self.logger.info('Results Server alive and listening....')

        # atexit function, shut down server
        atexit.register(self.killServer)

        # set up socket to communicate with dashboard (if specified)
        if settings['launchDashboard']:
            self.dashboard = True
            context = zmq.Context.instance()
            self.dashboardSocket = context.socket(zmq.REQ)
            self.dashboardSocket.connect('tcp://127.0.0.1:{}'.format(settings['dashboardPort']))
        else:
            self.dashboard = False

    def run(self):
        """ Run server, listening for requests and returning responses to clients

        """
        while self.alive:
            ### Listen for new connections, redirect clients to new socket
            connection, address = self.resultsSocket.accept()
            self.logger.debug('received connection from: {}'.format(address))

            ### Get the requested volume (should be a 4-char string representing
            # volume number, e.g. '0001')
            recvMsg = connection.recv(4).decode()

            # reformat the requested volume to remove any leading 0s
            requestedVol = str(int(recvMsg))
            self.logger.debug('Received Request for volIdx {}'.format(requestedVol))
            self.sendToDashboard(msgType='request', msg=recvMsg)

            ### Look up the results for the requested volume
            volResults = self.requestLookup(requestedVol)

            ### Send the results to the client
            self.sendResults(connection, volResults)
            self.logger.debug('Sent Response for volIdx {} : {}'.format(requestedVol, volResults))
            self.sendToDashboard(msgType='response', msg=volResults)

            # close client connection
            connection.close()

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
        self.logger.debug('volIdx {} added to resultsServer : {}'.format(volIdx, volResults))

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
        self.logger.debug('Sent result: {}'.format(formattedMsg))

    def sendToDashboard(self, msgType=None, msg=None):
        """ Send a msg to the Pyneal dashboard.

        The dashboard expects messages formatted in specific way, namely a
        dictionary with 2 keys: 'topic', and 'content'. In this case, the
        results server will always use the topic 'resultsServerLog' to
        make sure the message gets parsed correctly by the dashboard webserver.

        The 'content' will always be a dictionary that this function constructs
        based on the specified `msgType` and `msg`

        If `msgType` is 'request', `msg` should be the string containing the
        requested volume index.

        If `msgType` is 'response', `msg` should be the dictionary containing
        the results for the requested volume.

        Parameters
        ----------
        type : string {'request', 'response'}
            type of results server log message
        msg : string, or dict
            message/data to send to the results server log of the dashboard

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

    def saveResults(self):
        """ Save Results

        save all of the results to the output directory as results.json file
        """
        fname = join(self.seriesOutputDir, 'results.json')
        with open(fname, 'w') as outputFile:
            outputFile.write(json.dumps(self.results))

    def killServer(self):
        """ Close the thread by setting the alive flag to False """
        self.alive = False
        self.resultsSocket.close()


if __name__ == '__main__':
    # set up settings dict
    settings = {'resultsServerPort': 5556}

    resultsServer = ResultsServer(settings)
    # resultsServer.daemon = True
    resultsServer.start()
    print('Results Server alive and listening...')
