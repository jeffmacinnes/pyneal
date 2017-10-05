"""
Basic script to mimic the behavior of Pyneal during an actual scan.
This is a server to receive incoming slice files
"""

import sys, os
import time
import zmq
import dicom
import base64
import numpy as np
import nibabel as nib


host = 'localhost'
port = 50001


image_matrix = np.zeros(shape=(64, 64, 34, 10))	# build empty data matrix

context = zmq.Context.instance()
sock = context.socket(zmq.REP)
sock.connect('tcp://{}:{}'.format(host,port))
while True:

    # receive header info as json
    sliceInfo = sock.recv_json(flags=0)

    # retrieve relevant values about this slice
    sliceIdx = sliceInfo['sliceIdx']
    volIdx = sliceInfo['volIdx']
    sliceDtype = sliceInfo['dtype']
    sliceShape = sliceInfo['shape']

    # receive raw data stream, reshape to slice dimensions
    data = sock.recv(flags=0, copy=True, track=False)
    pixel_array = np.fromstring(data, dtype=sliceDtype)
    pixel_array = pixel_array.reshape(sliceShape)

    if volNum >= image_matrix.shape[3]:
        testImage = nib.Nifti1Image(image_matrix, affine=np.eye(4))
        testImage.to_filename('testImage.nii.gz')
        break

    # add the pixel data to the appropriate slice location
    image_matrix[:, :, sliceNum, volNum] = pixel_array

    # send slice over socket
    response = 'Received vol {}, slice {}'.format(volNum, sliceNum)
    sock.send_string(response)
    print(response)
