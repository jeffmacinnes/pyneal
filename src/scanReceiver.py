"""
Class to listen for incoming data from the scanner.

This tool is designed to be run in a separate thread, where it will:
    - establish a socket connection to pynealScanner (which will be sending slice
data from the scanner)
    - listen for incoming slice data (preceded by a header)
    - format the incoming data, and assign it to the proper location in a
    4D matrix for the entire san
In additiona, it also includes various methods for accessing the progress of an on-going scan, and returning data that has successfully arrived, etc.

--- Notes for setting up:
Socket Connection:
This tool uses the ZeroMQ library, instead of the standard python socket library.
ZMQ takes care of a lot of the backend work, is incredibily reliable, and offers
methods for easily sending pre-formatted types of data, including JSON dicts,
and numpy arrays.

Expectations for data formatting:
Once a scan has begun, this tool expects data to arrive over the socket
connection one slice at a time (though not necessarily in the proper
chronologic order).

There should be two parts to each slice transmission:
    1. First, a JSON header containing the following dict keys:
        - sliceIdx: within-volume index of the slice (0-based)
        - volIdx: volume index of the volume this slice belongs to (0-based)
        - sliceDtype: datatype of the slice pixel data (e.g. int16)
        - sliceShape: slice pixel dimensions (e.g. (64, 64))
    2. Next, the slice pixel data, as a string buffer.

Once both of those peices of data have arrived, this tool will send back a
confirmation string message.

Slice Orientation:
This tools presumes that arriving slices have been reoriented to RAS+
This is a critical premise for downstream analyses, so MAKE SURE the
slices are oriented in that way on the pynealScanner side before sending.
"""
# python2/3 compatibility
from __future__ import print_function

import os
import sys
import threading

import numpy as np
import zmq

# ADD LOGGING

# HAVE IT BUILD EMPTY MATRIX BASED ON INFO FROM FIRST INCOMING SLICE

# SET UP ZMQ PUBLISH SOCKET FOR SENDING MESSASGES OUT ABOUT VOLUMES
# THAT HAVE ARRIVED




class ScanReceiver(threading.Thread):
    """
    Class to listen in for incoming scan data. As new slices
    arrive, the header is decoded, and the slice is added to
    the appropriate place in the 4D data matrix

    input args:
        nTmpts: number of expected timepoints in series [500]
        host: host IP for scanner socket ['127.0.0.1']
        port: port # for scanner socket [5555]
    """

    def __init__(self, nTmpts=500, host='127.0.0.1', port=5555):
        threading.Thread.__init__(self)

        # class config vars
        self.host = host
        self.port = port

        # initiate socket
        context = zmq.Context.instance()
        self.socket = context.socket(zmq.PAIR)
        self.socket.connect('tcp://{}:{}'.format(self.host, self.port))

    def run(self):
        # make contact with scanner socket
        while True:
            self.socket.send_string('open')
            msg = self.socket.recv_string()
            break
        print('scanner socket opened...')

        # ------------------------------------
        # Listen to incoming data
        while True:
            sliceInfo = self.socket.recv_json(flags=0)
            sliceDtype = sliceInfo['dtype']
            sliceShape = sliceInfo['shape']
            print(sliceInfo.keys())

            data = self.socket.recv(flags=0, copy=False, track=False)
            pixel_array = np.frombuffer(data, dtype=sliceDtype)
            pixel_array = pixel_array.reshape(sliceShape)

            print(pixel_array.shape)

            self.socket.send_string('got it')


    def get_vol(self, volIdx):
        """
        Return the requested vol, if it is here.
        Note: volIdx is 0-based
        """
        pass


    def get_slice(self, volIdx, sliceIdx):
        """
        Return the requested slice, if it is here.
        Note: volIdx, and sliceIdx are 0-based
        """
        pass







host = '127.0.0.1'
port = 5555

if __name__ == '__main__':
    scanReceiver = ScanReceiver(host, port)
    scanReceiver.start()
