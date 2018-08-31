import os
from os.path import join
import sys
import socket
import json

import zmq
import numpy as np
import nibabel as nib

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

    # Set up Pyneal Scanner simulator for making a connection to the scanReceiver
    context = zmq.Context.instance()
    socket = context.socket(zmq.PAIR)
    socket.connect('tcp://{}:{}'.format(host, port))

    while True:
        msg = 'hello from test pyneal scanner simulator'
        socket.send_string(msg)
        resp = socket.recv_string()
        if resp == msg:
            break

    # Send data to scan receiver
    ds = nib.load(join(paths['testDataDir'], 'testSeries.nii.gz'))
    ds_array = ds.get_data()
    ds_affine = ds.affine

    for volIdx in range(ds_array.shape[3]):
        # grab this volume from the dataset
        thisVol = np.ascontiguousarray(ds_array[:, :, :, volIdx])

        # build header
        volHeader = {'volIdx': volIdx,
                     'dtype': str(thisVol.dtype),
                     'shape': thisVol.shape,
                     'affine': json.dumps(ds_affine.tolist()),
                     'TR': str(1000)}

        # send header as json
        socket.send_json(volHeader, zmq.SNDMORE)

        # now send the voxel array for this volume
        socket.send(thisVol, flags=0, copy=False, track=False)

        # list for response
        socketResponse = socket.recv_string()

    # test scanReceiver get functions
    np.testing.assert_equal(scanReceiver.get_affine(), ds_affine)
    np.testing.assert_equal(scanReceiver.get_slice(1,10), ds_array[:, :, 10, 1])
    np.testing.assert_equal(scanReceiver.get_vol(2), ds_array[:, :, :, 2])

    # test saving (then delete)
    scanReceiver.saveResults()
    os.remove(join(paths['testDataDir'], 'receivedFunc.nii.gz'))

    # assuming nothing crashed, shutdown scanReceiver server
    scanReceiver.killServer()
