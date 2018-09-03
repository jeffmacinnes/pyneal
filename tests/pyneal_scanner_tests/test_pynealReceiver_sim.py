import os
from os.path import join
import sys
import threading
import json

import zmq
import numpy as np

import pynealScanner_helper_tools as helper_tools

# get dictionary with relevant paths for tests within this module
paths = helper_tools.get_pyneal_scanner_test_paths()
for path in [paths['pynealDir'], paths['pynealScannerDir']]:
    if path not in sys.path:
        sys.path.insert(0, path)

import pyneal_scanner.simulation.pynealReceiver_sim as pynealReceiver_sim
import pyneal_scanner.utils.general_utils as general_utils

def test_pynealReceiver_sim():
    """ Test pyneal_scanner.simulation.pynealReceiver_sim module """

    port = 5555
    nVols = 3

    # launch pynealReceiver_sim in background thread
    t = threading.Thread(target=pynealReceiver_sim.launchPynealReceiver,
                          args=(port, nVols),
                          kwargs={'saveImage':False})
    t.start()

    # create the socket that we'll use to send data to pynealReceiver_sim
    pyneal_socket = general_utils.create_pynealSocket('127.0.0.1', port)
    msg = 'hello from pynealReceiver_sim test'
    pyneal_socket.send_string(msg)
    msgResponse = pyneal_socket.recv_string()

    # send fake data to pynealReceiver_sim thread
    imageData = (np.random.rand(64, 64, 18, nVols)*100).astype(np.uint16)
    for volIdx in range(nVols):
        # extract this volume
        thisVol = imageData[:, :, :, volIdx]

        # build header
        volHeader = {
            'volIdx': volIdx,
            'TR': 1,
            'dtype': str(thisVol.dtype),
            'shape': thisVol.shape,
            'affine': json.dumps(np.eye(4).tolist())}

        # send the header to pynealReceiver_sim
        pyneal_socket.send_json(volHeader, zmq.SNDMORE)

        # send data to pynealRecevier_sim
        thisVol = np.ascontiguousarray(thisVol)
        pyneal_socket.send(thisVol, flags=0, copy=False, track=False)
        resp = pyneal_socket.recv_string()
