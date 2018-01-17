"""
Class to listen for incoming data from the scanner.

This tool is designed to be run in a separate thread, where it will:
    - establish a socket connection to pynealScanner (which will be sending volume
data from the scanner)
    - listen for incoming volume data (preceded by a header)
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
connection one volume at a time.

There should be two parts to each volume transmission:
    1. First, a JSON header containing the following dict keys:
        - volIdx: within-volume index of the volume (0-based)
        - dtype: datatype of the voxel array (e.g. int16)
        - shape: voxel array dimensions  (e.g. (64, 64, 18))
        - affine: affine matrix to transform the voxel data from vox to mm space
    2. Next, the voxel array, as a string buffer that can be converted into a
        numpy array.

Once both of those peices of data have arrived, this tool will send back a
confirmation string message.

** Volume Orientation:
Pyneal works on the assumption that incoming volumes will have the 3D
voxel array ordered like RAS+, and that the accompanying affine will provide
a transform from voxel space RAS+ to mm space RAS+. In order to any mask-based
analysis in Pyneal to work, we need to make sure that the incoming data and the
mask data are reprsented in the same way. The pyneal_scanner utilities have all
been configured to ensure that each volume that is transmitted is in RAS+ space.

Along those same lines, the affine that gets transmitted in the header for each
volume should be the same for all volumes in the series.
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
    Class to listen in for incoming scan data. As new volumes
    arrive, the header is decoded, and the volume is added to
    the appropriate place in the 4D data matrix

    input args:
        numTimepts: number of expected timepoints in series [500]
        host: host IP for scanner socket ['127.0.0.1']
        port: port # for scanner socket [5555]
    """
    def __init__(self, numTimepts=500, host='*', port=5555):
        # start the thread upon creation
        Thread.__init__(self)

        # set up logger
        self.logger = logging.getLogger('PynealLog')

        # class config vars
        self.scanStarted = False
        self.numTimepts = numTimepts    # total number of vols (or timepts) expected
        self.alive = True               # thread status
        self.imageMatrix = None         # matrix that will hold the incoming data
        self.affine = None

        # array to keep track of completedVols
        self.completedVols = np.zeros(self.numTimepts, dtype=bool)

        # set up socket to communicate with scanner
        context = zmq.Context.instance()
        self.scannerSocket = context.socket(zmq.PAIR)
        self.scannerSocket.bind('tcp://{}:{}'.format(host, port))
        self.logger.debug('scanReceiver server bound to {}:{}'.format(host, port))


    def run(self):
        # Once this thread is up and running, confirm that the scanner socket
        # is alive and working before proceeding.
        while True:
            print('Waiting for connection from pyneal_scanner')
            msg = self.scannerSocket.recv_string()
            print('Received message: ', msg)
            self.scannerSocket.send_string(msg)
            break
        self.logger.debug('Scanner socket connected to Pyneal-Scanner')

        # Start the main loop to listen for new data
        while self.alive:
            # wait for json header to appear. The header is assumed to
            # have key:value pairs for:
            # volIdx - volume index (0-based)
            # dtype - dtype of volume voxel array
            # shape - dims of volume voxel array
            # affine - affine to transform vol to RAS+ mm space
            volHeader = self.scannerSocket.recv_json(flags=0)

            # if this is the first vol, initialize the matrix and store the affine
            if not self.scanStarted:
                self.createImageMatrix(volHeader)
                self.affine = volHeader['affine']

                self.scanStarted = True     # toggle the scanStarted flag

            # now listen for the image data as a string buffer
            voxelArray = self.scannerSocket.recv(flags=0, copy=False, track=False)

            # format the voxel array according to params from the vol header
            voxelArray = np.frombuffer(voxelArray, dtype=volHeader['dtype'])
            voxelArray = voxelArray.reshape(volHeader['shape'])

            # add the volume to the appropriate location in the image matrix
            volIdx = volHeader['volIdx']
            self.imageMatrix[:,:, :, volIdx] = voxelArray

            # update the completed volumes table
            self.completedVols[volIdx] = True

            # send response back to Pyneal-Scanner
            response = 'Received vol {}'.format(volIdx)
            self.scannerSocket.send_string(response)
            self.logger.info(response)


    def createImageMatrix(self, volHeader):
        """
        Once the first volume appears, this function should be called
        to build the empty matrix to store incoming vol data, using
        info from the vol header.
        """
        # create the empty imageMatrix
        self.imageMatrix = np.zeros(shape=(
                                volHeader['shape'][0],
                                volHeader['shape'][1],
                                volHeader['shape'][2],
                                self.numTimepts), dtype=volHeader['dtype'])

        self.logger.debug('Image Matrix dims: {}'.format(self.imageMatrix.shape))


    def get_affine(self):
        """
        Return the affine for this series
        """
        return self.affine


    def get_vol(self, volIdx):
        """
        Return the requested vol, if it is here.
        Note: volIdx is 0-based
        """
        if self.completedVols[volIdx]:
            return self.imageMatrix[:, :, :, volIdx]
        else:
            return None


    def get_slice(self, volIdx, sliceIdx):
        """
        Return the requested slice, if it is here.
        Note: volIdx, and sliceIdx are 0-based
        """
        if self.completedVols[volIdx]:
            return self.imageMatrix[:, :, sliceIdx, volIdx]
        else:
            return None


    def stop(self):
        # function to stop the Thread
        self.alive = False


if __name__ == '__main__':
    host = '*'
    port = 5555

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
    scanReceiver = ScanReceiver(numTimepts=100, host=host, port=port)
    scanReceiver.start()
