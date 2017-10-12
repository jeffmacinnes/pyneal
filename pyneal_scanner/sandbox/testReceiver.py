"""
Basic script to mimic the behavior of Pyneal during an actual scan.
This is a server to receive incoming slice files
"""
from __future__ import division

import sys, os
import time
import zmq
import dicom
import base64
import numpy as np
import nibabel as nib


host = 'localhost'
port = 50001


image_matrix = np.zeros(shape=(64, 64, 18, 10))	# build empty data matrix (xyzt)

context = zmq.Context.instance()
sock = context.socket(zmq.REP)
sock.connect('tcp://{}:{}'.format(host,port))
print('here')

slice1_pos = None
slice1_or = None
sliceEnd_pos = None
sliceEnd_or = None

while True:

    # receive header info as json
    sliceInfo = sock.recv_json(flags=0)

    # retrieve relevant values about this slice
    sliceIdx = sliceInfo['sliceIdx']
    volIdx = sliceInfo['volIdx']
    sliceDtype = sliceInfo['dtype']
    sliceShape = sliceInfo['shape']
    imagePosition = sliceInfo['imagePosition']
    imageOrientation = sliceInfo['imageOrientation']
    print(type(imagePosition[0]))
    #print(imagePosition)


    if slice1_pos is None:
        if sliceIdx == 0:
            slice1_pos = np.asarray(imagePosition)
    if slice1_or is None:
        if sliceIdx == 0:
            slice1_or = np.asarray(imageOrientation)
    if sliceEnd_pos is None:
        if sliceIdx == 17:
            sliceEnd_pos = np.asarray(imagePosition)
    if sliceEnd_or is None:
        if sliceIdx == 17:
            sliceEnd_or = np.asarray(imageOrientation)

    # receive raw data stream, reshape to slice dimensions
    data = sock.recv(flags=0, copy=False, track=False)
    pixel_array = np.frombuffer(data, dtype=sliceDtype)
    pixel_array = pixel_array.reshape(sliceShape)
    print('origin received: {}'.format(pixel_array[0,0]))

    if volIdx >= image_matrix.shape[3]:

        ### THIS WORKS - MAKE MORE ELEGANT
        # create affine
        imgOr = slice1_or*3.75
        affine = np.zeros(shape=(4,4))
        affine[0,0] = imgOr[3]
        affine[1,0] = imgOr[4]
        affine[2,0] = imgOr[5]
        affine[0,1] = imgOr[0]
        affine[1,1] = imgOr[1]
        affine[2,1] = imgOr[2]

        affine[0,2] = (slice1_pos[0] - sliceEnd_pos[0])/(1-17)
        affine[1,2] = (slice1_pos[1] - sliceEnd_pos[1])/(1-17)
        affine[2,2] = (slice1_pos[2] - sliceEnd_pos[2])/(1-17)

        affine[0,3] = slice1_pos[0]
        affine[1,3] = slice1_pos[1]
        affine[2,3] = slice1_pos[2]

        affine[3,3] = 1

        testImage = nib.Nifti1Image(image_matrix, affine=affine)
        testImage.to_filename('testImage1.nii.gz')
        break

    # add the pixel data to the appropriate slice location
    image_matrix[:, :, sliceIdx, volIdx] = pixel_array

    # send slice over socket
    response = 'Received vol {}, slice {}'.format(volIdx, sliceIdx)
    sock.send_string(response)
    print(response)
