"""
Simulate the socket server that pynealScanner would use to send out slice data
during a real scan

Set the scan parameters below to indicate the dimensions of your
simulated data (i.e. slice dimensions, number of slices per volume,
number of timepts)

Each slice will be composed of randomly generated values
"""
# python 2/3 compatibility
from __future__ import print_function
from __future__ import division

import os
import time

import zmq
import numpy as np

### --- Scan Parameters ---
sliceShape = (64,64)
nSlicesPerVol = 18
nTmpts = 5
TR = 1           # set TR in s (or None for as fast as possible)
### ----------------------

# build dataset of random integers, formatted at dtype='int16'
fakeDataset = np.random.random((sliceShape[0],
                    sliceShape[1],
                    nSlicesPerVol,
                    nTmpts)).astype('int16')

# Set up host and port for the socket
port = 5555
host = '127.0.0.1'

# Create socket, bind to address
context = zmq.Context.instance()
socket = context.socket(zmq.PAIR)
socket.connect('tcp://{}:{}'.format(host, port))

# Wait for pyneal (e.g. client) to connect to the socket
print('waiting for connection...')
while True:
    msg = socket.recv_string()
    print(msg)
    if msg[:4] == 'open':
        socket.send_string(msg)
        break

# Start sending data!
for vol in range(nTmpts):
    for slc in range(nSlicesPerVol):
        # grab this slice from the dataset
        slice_pixels = np.ascontiguousarray(fakeDataset[:,:,slc,vol])

        # build header
        sliceHeader = {
                'dtype':str(slice_pixels.dtype),
                'shape':slice_pixels.shape,
                'volIdx': vol,
                'sliceIdx':slc,
                'nSlicesPerVol':nSlicesPerVol
                }

        # send header as json
        socket.send_json(sliceHeader, zmq.SNDMORE)

        # now send the pixel array for this slice
        socket.send(slice_pixels, flags=0, copy=False, track=False)

        # list for response
        socketResponse = socket.recv_string()
        print('Socket Response: {}'.format(socketResponse))

        if TR is not None:
            time.sleep(TR/nSlicesPerVol)
