import os
from os.path import join
import sys
import socket
import subprocess
import json

import numpy as np

import pyneal_helper_tools as helper_tools

# get dictionary with relevant paths for tests within this module
paths = helper_tools.get_pyneal_test_paths()
if paths['pynealDir'] not in sys.path:
        sys.path.insert(0, paths['pynealDir'])
socketPort = 5556

def test_endUser_sim():
    """ test utils.endUser_sim """

    ### Initialize the results server to listen for requests from endUser_sim
    from src.resultsServer import ResultsServer
    # create settings dictionary
    settings = {'resultsServerPort': socketPort,
                'pynealHost': '127.0.0.1',
                'seriesOutputDir': paths['testDataDir'],
                'launchDashboard': False}
    resultsServer = ResultsServer(settings)
    resultsServer.daemon = True
    resultsServer.start()

    # populate the results server with fake values
    fakeResults = np.array([1000.1, 1000.2, 1000.3])
    for volIdx in range(3):
        thisResult = {'testResult': fakeResults[volIdx]}
        resultsServer.updateResults(volIdx, thisResult)

    # User endUser_sim to retrieve the values you just put in the resultsServer
    for volIdx in range(3):
        process = subprocess.Popen(['python3',
                            join(paths['pynealDir'], 'utils/simulation/endUser_sim.py'),
                            str(volIdx)], stdout=subprocess.PIPE)
        out, err = process.communicate()
        result = parseOutput(out.decode("utf-8"))

        # confirm results match
        assert result == fakeResults[volIdx]

    # shutdown the results server
    resultsServer.killServer()




def parseOutput(outputMsg):
    """ parse the full stdOut from call to endUser_sim to get the returned result """
    resultStr = outputMsg.split('\n')[-2]
    resultStr = resultStr.replace("'", '"')       # make single quotes double
    resultStr = resultStr.replace('True', '"True"') # put quotes around 'True'
    resultDict = json.loads(resultStr)
    return resultDict['testResult']
