"""
Basic script to mimic the behavior of Pyneal during an actual scan.
This is a server to receive incoming slice files
"""
from __future__ import division

import os
import sys
import time
import zmq
import dicom
import base64
import numpy as np
import nibabel as nib


host = 'localhost'
port = 5555


image_matrix = np.zeros(shape=(64, 64, 18, 10))	# build empty data matrix (xyzt)

context = zmq.Context.instance()
sock = context.socket(zmq.REP)
sock.connect('tcp://{}:{}'.format(host,port))

# wait for initial contact
while True:
    msg = sock.recv_string()
    sock.send_string(msg)
    break

print('Waiting for slice data to appear...')


while True:

    # receive header info as json
    sliceInfo = sock.recv_json(flags=0)

    # retrieve relevant values about this slice
    sliceIdx = sliceInfo['sliceIdx']
    volIdx = sliceInfo['volIdx']
    sliceDtype = sliceInfo['dtype']
    sliceShape = sliceInfo['shape']

    # receive raw data stream, reshape to slice dimensions
    data = sock.recv(flags=0, copy=False, track=False)
    pixel_array = np.frombuffer(data, dtype=sliceDtype)
    pixel_array = pixel_array.reshape(sliceShape)

    # add the pixel data to the appropriate slice location
    image_matrix[:, :, sliceIdx, volIdx] = pixel_array

    # send slice over socket
    response = 'Received vol {}, slice {}'.format(volIdx, sliceIdx)
    sock.send_string(response)
    print(response)
