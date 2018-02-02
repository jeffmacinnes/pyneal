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
import json
import base64
import numpy as np
import nibabel as nib


host = '*'
port = 5556

nVols = 60
firstVolHasArrived = False

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

    # build the imageMatrix if this is the first volume
    if not firstVolHasArrived:
        imageMatrix = np.zeros(shape=(volShape[0],
                                volShape[1],
                                volShape[2],
                                nVols), dtype=volDtype)
        volAffine = np.array(json.loads(volInfo['affine']))

        # update first vol flag
        firstVolHasArrived = True

    # receive raw data stream, reshape to slice dimensions
    data = sock.recv(flags=0, copy=False, track=False)
    voxelArray = np.frombuffer(data, dtype=volDtype)
    voxelArray = voxelArray.reshape(volShape)

    # add the voxel data to the appropriate location
    imageMatrix[:, :, :, volIdx] = voxelArray

    # send slice over socket
    if volIdx == (nVols-1):
        response = 'Received vol {} - STOP'.format(volIdx)
    else:
        response = 'Received vol {}'.format(volIdx)
    sock.send_string(response)
    print(response)

    # if all volumes have arrived, save the image
    if volIdx == (nVols-1):
        receivedImg = nib.Nifti1Image(imageMatrix, volAffine)
        outputName = 'receivedImg.nii.gz'
        nib.save(receivedImg, outputName)

        print('Done. Image saved at: {}'.format(outputName))
        break
