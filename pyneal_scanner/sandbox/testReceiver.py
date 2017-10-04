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


host = 'localhost'
port = 50001


context = zmq.Context.instance()
sock = context.socket(zmq.REP)
sock.connect('tcp://{}:{}'.format(host,port))
while True:

    # receive header info as json
    sliceInfo = sock.recv_json(flags=0)

    # receive raw data stream
    data = sock.recv(flags=0, copy=True, track=False)
    pixel_array = np.fromstring(data, dtype=sliceInfo['dtype'])
    pixel_array.reshape(sliceInfo['shape'])

    sliceNum = sliceInfo['sliceNum']
    volNum = sliceInfo['volNum']

    # send slice over socket
    response = 'Received: vol {}, slice {}'.format(volNum, sliceNum)
    sock.send_string(response)
    print(response)
