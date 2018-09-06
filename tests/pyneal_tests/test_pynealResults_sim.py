import os
from os.path import join
import sys
import socket
import subprocess
import json
import importlib

import numpy as np

import pyneal_helper_tools as helper_tools

# get dictionary with relevant paths for tests within this module
paths = helper_tools.get_pyneal_test_paths()
if paths['pynealDir'] not in sys.path:
        sys.path.insert(0, paths['pynealDir'])

# import the pynealResults_sim module
spec = importlib.util.spec_from_file_location("pynealResults_sim",
            join(paths['pynealDir'], 'utils/simulation/pynealResults_sim.py'))
pynealResults_sim = importlib.util.module_from_spec(spec)
spec.loader.exec_module(pynealResults_sim)

TR = 0
host = '127.0.0.1'
port = 5556

class Test_launchPynealSim():
    """ test for utils.simulation.pynealResults_sim """

    def test_launchPynealSim(self):
        """ test pynealResults_sim.launchPynealSim

        test the function that launches the simulator and populates it with
        fake data all in one method
        """
        pynealResults_sim.launchPynealSim(TR, host, port, keepAlive=False)

    def test_pynealResultsSim_resultsServer(self):
        """ test pynealResults_sim.ResultsServer

        test the class the actually runs the simulated results server
        """
        # launch the simulated results server
        settings = {'pynealHost': host, 'resultsServerPort': port}
        resultsServer = pynealResults_sim.ResultsServer(settings)
        resultsServer.daemon = True
        resultsServer.start()

        # test updating the results server with results
        fakeResults = np.array([5000.1, 5000.2, 5000.3])
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

        # assuming nothing crashed, close the socket
        resultsServer.killServer()


def fakeEndUserRequest(requestedVolIdx):
    """ Function to mimic the behavior of the end user, which sends a request
    to the simulated results server

    Parameters
    ----------
    volIdx : int
        the volIdx of the volume you'd like to request results for

    """
    # socket configs
    host = '127.0.0.1'  # ip of where Pyneal is running

    # connect to the results server of Pyneal
    clientSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    clientSocket.connect((host, port))

    # send request for volume number. Request must by 4-char string representing
    # the volume number requested
    request = str(requestedVolIdx).zfill(4)
    clientSocket.send(request.encode())

    # When the results server recieved the request, it will send back a variable
    # length response. But first, it will send a header indicating how long the response
    # is. This is so the socket knows how many bytes to read
    hdr = ''
    while True:
        nextChar = clientSocket.recv(1).decode()
        if nextChar == '\n':
            break
        else:
            hdr += nextChar
    msgLen = int(hdr)

    # now read the full response from the server
    serverResp = clientSocket.recv(msgLen)
    clientSocket.close()

    # format at JSON
    serverResp = json.loads(serverResp.decode())
    return serverResp
