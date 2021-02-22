import os
from os.path import join
import sys
import socket
import json

import numpy as np

import pyneal_helper_tools as helper_tools

# get dictionary with relevant paths for tests within this module
paths = helper_tools.get_pyneal_test_paths()
if paths['pynealDir'] not in sys.path:
        sys.path.insert(0, paths['pynealDir'])
socketPort = 5556

from src.resultsServer import ResultsServer

# Tests for functions within the resultsServer module
def test_resultsServer():
    """ tests pyneal.src.resultsServer """

    # create settings dictionary
    settings = {'resultsServerPort': socketPort,
                'pynealHost': '127.0.0.1',
                'seriesOutputDir': paths['testDataDir'],
                'launchDashboard': False}
    resultsServer = ResultsServer(settings)
    resultsServer.daemon = True
    resultsServer.start()

    # test updating the results server with results
    fakeResults = np.array([1000.1, 1000.2, 1000.3])
    for volIdx in range(3):
        thisResult = {'testResult': fakeResults[volIdx]}
        resultsServer.updateResults(volIdx, thisResult)

    # test retrieving values from the results server
    for volIdx in range(3):
        result = resultsServer.requestLookup(volIdx)
        assert result['testResult'] == fakeResults[volIdx]

    # test sending a request from a remote socket connection
    requestedVolIdx = 1     # vol that exists
    result = fakeEndUserRequest(requestedVolIdx)
    assert result['foundResults'] == True
    assert result['testResult'] == fakeResults[requestedVolIdx]

    requestedVolIdx = 99    # vol that doesn't exist
    result = fakeEndUserRequest(requestedVolIdx)
    assert result['foundResults'] == False

    # test saving data
    resultsServer.saveResults()
    os.remove(join(paths['testDataDir'], 'results.json'))

    # assuming nothing as crashed, close the socket
    resultsServer.killServer()



def fakeEndUserRequest(requestedVolIdx):
    """ Function to mimic the behavior of the end user, which sends a request
    to the results server

    Parameters
    ----------
    volIdx : int
        the volIdx of the volume you'd like to request results for

    """
    # socket configs
    host = '127.0.0.1'  # ip of where Pyneal is running

    # connect to the results server of Pyneal
    clientSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    clientSocket.connect((host, socketPort))

    # send request for volume number. Request must by 4-char string representing
    # the volume number requested
    request = str(requestedVolIdx).zfill(4)
    clientSocket.send(request.encode())

    # now read the full response from the server
    resp = b''
    while True:
        serverData = clientSocket.recv(1024)
        if serverData:
            resp += serverData
        else: 
            break

    clientSocket.close()

    # format at JSON
    resp = json.loads(resp.decode())
    return resp
