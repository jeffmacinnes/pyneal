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
** Socket Connection:
This tool uses the ZeroMQ library, instead of the standard python socket library.
ZMQ takes care of a lot of the backend work, is incredibily reliable, and offers
methods for easily sending pre-formatted types of data, including JSON dicts,
and numpy arrays.

** Expectations for data formatting:
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

** Slice Orientation:
This tools presumes that arriving slices have been reoriented to RAS+
This is a critical premise for downstream analyses, so MAKE SURE the
slices are oriented in that way on the pynealScanner side before sending.

In addition, the numpy arrays are presumed to be indexed like [X,Y]. This is
the opposite of how numpy would default to storing image data (default is
[rows, cols], which is [y,x] in cartesian coords). So, make sure this
assumption holds as well
"""
# python2/3 compatibility
from __future__ import print_function

import os
import sys
from threading import Thread
import logging

import numpy as np
import zmq

# SET UP ZMQ PUBLISH SOCKET FOR SENDING MESSASGES OUT ABOUT VOLUMES
# THAT HAVE ARRIVED


class ScanReceiver(Thread):
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
        # start the thread upon creation
        Thread.__init__(self)

        # set up logger
        self.logger = logging.getLogger(__name__)

        # class config vars
        self.nTmpts = nTmpts        # total number of vols (or timepts) expected
        self.alive = True           # thread status
        self.imageMatrix = None     # matrix that will hold the incoming data
        self.completedSlices = None # nSlices x nVols matrix that will store bools
                                    # indicating whether each slice has arrived

        # set up socket to communicate with scanner
        context = zmq.Context.instance()
        self.scannerSocket = context.socket(zmq.PAIR)
        self.scannerSocket.connect('tcp://{}:{}'.format(host, port))
        self.logger.debug('scanReceiver connecting to host: {}, port: {}'.format(host, port))

    def run(self):
        # Once this thread is up and running, confirm that the scanner socket
        # is alive and working before proceeding.
        while True:
            self.scannerSocket.send_string('open')
            msg = self.scannerSocket.recv_string()
            break
        self.logger.debug('Scanner socket connected to Pyneal-Scanner')

        # Start the main loop to listen for new data
        while self.alive:
            # wait for json header to appear. The header is assumed to
            # have key:value pairs for:
            # sliceIdx - slice index (0-based)
            # volIdx - volume index (0-based)
            # nSlicesPerVol - total slices per vol
            # dtype - dtype of slice pixel data
            # shape - dims of slice pixel data
            sliceHeader = self.scannerSocket.recv_json(flags=0)

            # if this is the first slice, initialize the matrix
            # and the completedVols table
            if self.imageMatrix is None:
                self.scanStarted = True
                self.createDataMatrix(sliceHeader)

            # now listen for the image data as a string buffer
            pixel_array = self.scannerSocket.recv(flags=0, copy=False, track=False)

            # format the pixel array according to params from the slice header
            pixel_array = np.frombuffer(pixel_array, dtype=sliceHeader['dtype'])
            pixel_array = pixel_array.reshape(sliceHeader['shape'])

            # add the slice to the appropriate location in the image matrix
            sliceIdx = sliceHeader['sliceIdx']
            volIdx = sliceHeader['volIdx']
            self.imageMatrix[:,:, sliceIdx, volIdx]

            # update the completed slices table
            self.completedSlices[sliceIdx, volIdx] = True

            # send response back to Pyneal-Scanner
            response = 'Received vol {}, slice {}'.format(volIdx, sliceIdx)
            self.scannerSocket.send_string(response)
            self.logger.info(response)


    def createDataMatrix(self, sliceHeader):
        """
        Once the first slice appears, this function should be called
        to build the empty matrix to store incoming slice data, using
        info from the slice header. Also, build the table that will
        store T/F values for whether each slice has appeared
        """
        # create the empty imageMatrix (note: nTmpts is NOT in the slice header)
        self.imageMatrix = np.zeros(shape=(
                                sliceHeader['shape'][0],
                                sliceHeader['shape'][1],
                                sliceHeader['nSlicesPerVol'],
                                self.nTmpts))

        # create the table for indicated arrived slices
        self.completedSlices = np.zeros(shape=(
                                sliceHeader['nSlicesPerVol'],
                                self.nTmpts), dtype=bool)

        self.logger.debug('Image Matrix dims: {}'.format(self.imageMatrix.shape))


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

    def stop(self):
        # function to stop the Thread
        self.alive = False




host = '127.0.0.1'
port = 5555

if __name__ == '__main__':
    ### set up logging
    fileLogger = logging.FileHandler('./scanReceiver.log', mode='w')
    fileLogger.setLevel(logging.DEBUG)
    fileLogFormat = logging.Formatter('%(asctime)s - %(levelname)s - %(threadName)s - %(module)s, line: %(lineno)d - %(message)s',
                                        '%m-%d %H:%M:%S')
    fileLogger.setFormatter(fileLogFormat)

    #
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)
    logger.addHandler(fileLogger)

    # start the scanReceiver
    scanReceiver = ScanReceiver(nTmpts=100, host=host, port=port)
    scanReceiver.start()
