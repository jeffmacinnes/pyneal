import os
from os.path import join
import sys
import socket
import json

import zmq
import numpy as np

import helper_tools

# get dictionary with relevant paths for tests within this module
paths = helper_tools.get_pyneal_scanner_test_paths()
sys.path.insert(0, paths['pynealDir'])

port = 5555
host = '127.0.0.1'


from src.scanReceiver import ScanReceiver

# Tests for functions within the resultsServer module
def test_resultsServer():
    """ tests pyneal.src.resultsServer """

    # create settings dictionary
    settings = {'pynealScannerPort': port,
                'pynealHost': host,
                'numTimepts': 3,
                'launchDashboard': False,
                'seriesOutputDir': paths['testDataDir']}
    scanReceiver = ScanReceiver(settings)
    scanReceiver.daemon = True
    scanReceiver.start()

    # Simulate Pyneal Scanner making a connection to the scanReceiver
    context = zmq.Context.instance()
    socket = context.socket(zmq.PAIR)
    socket.connect('tcp://{}:{}'.format(host, port))

    while True:
        msg = 'hello from test pyneal scanner simulator'
        socket.send_string(msg)

        resp = socket.recv_string()
        if resp == msg:
            break
