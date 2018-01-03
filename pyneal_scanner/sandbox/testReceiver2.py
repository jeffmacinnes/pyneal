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


host = '*'
port = 5555


#image_matrix = np.zeros(shape=(64, 64, 18, 60))	# build empty data matrix (xyzt)

context = zmq.Context.instance()
sock = context.socket(zmq.PAIR)
sock.bind('tcp://{}:{}'.format(host,port))

# wait for initial contact
while True:
    msg = sock.recv_string()
    sock.send_string(msg)
    break

print('Waiting for volume data to appear...')


while True:

    # receive header info as json
    volInfo = sock.recv_json(flags=0)

    # retrieve relevant values about this slice
    volIdx = volInfo['volIdx']
    volDtype = volInfo['dtype']
    volShape = volInfo['shape']
    volAffine = volInfo['affine']

    # receive raw data stream, reshape to slice dimensions
    data = sock.recv(flags=0, copy=False, track=False)
    voxelArray = np.frombuffer(data, dtype=volDtype)
    voxelArray = voxelArray.reshape(volShape)

    print(voxelArray.shape)

    # add the pixel data to the appropriate slice location
    #image_matrix[:, :, sliceIdx, volIdx] = pixel_array

    # send slice over socket
    response = 'Received vol {}'.format(volIdx)
    sock.send_string(response)
    print(response)
