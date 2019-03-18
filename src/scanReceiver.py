""" Class to listen for incoming data from the scanner.

This tool is designed to be run in a separate thread, where it will:
    - establish a socket connection to pynealScanner (which will be sending
    volume data from the scanner)
    - listen for incoming volume data (preceded by a header)
    - format the incoming data, and assign it to the proper location in a
    4D matrix for the entire san

In additiona, it also includes various methods for accessing the progress of an
on-going scan, and returning data that has successfully arrived, etc.

Notes for setting up:
** Socket Connection:
This tool uses the ZeroMQ library, instead of the standard python socket
library. ZMQ takes care of a lot of the backend work, is incredibily reliable,
and offers methods for easily sending pre-formatted types of data, including
JSON dicts, and numpy arrays.

** Expectations for data formatting:
Once a scan has begun, this tool expects data to arrive over the socket
connection one volume at a time.

There should be two parts to each volume transmission:
    1. First, a JSON header containing the following dict keys:
        - volIdx: within-volume index of the volume (0-based)
        - TR: repetition time for scan (seconds)
        - dtype: datatype of the voxel array (e.g. int16)
        - shape: voxel array dimensions  (e.g. (64, 64, 18))
        - affine: affine matrix to transform the voxel data from vox to mm
        space
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
been configured to ensure that each volume that is transmitted is in RAS+
space.

Along those same lines, the affine that gets transmitted in the header for each
volume should be the same for all volumes in the series.

"""
from os.path import join
from threading import Thread
import logging
import json
import atexit

import numpy as np
import nibabel as nib
import zmq


class ScanReceiver(Thread):
    """ Class to listen in for incoming scan data.

    As new volumes arrive, the header is decoded, and the volume is added to
    the appropriate place in the 4D data matrix

    Input a dictionary called 'settings' that has (at least) the following keys:
        numTimepts: number of expected timepoints in series [500]
        pynealHost: ip address for the computer running Pyneal
        pynealScannerPort: port # for scanner socket [e.g. 5555]

    """
    def __init__(self, settings):
        """ Initialize the class

        Parameters
        ----------
        settings : dict
            dictionary that contains all of the Pyneal settings for the current
            session. This dictionary is loaded by Pyneal is first launched. At
            a minumum, this dictionary must have the following keys:
                numTimepts: number of expected timepoints in series
                pynealHost: ip address for the computer running Pyneal
                pynealScannerPort: port # for scanner socket [e.g. 5555]

        """
        # start the thread upon creation
        Thread.__init__(self)

        # set up logger
        self.logger = logging.getLogger('PynealLog')

        # get vars from settings dict
        self.numTimepts = settings['numTimepts']
        self.host = settings['pynealHost']
        self.scannerPort = settings['pynealScannerPort']
        self.seriesOutputDir = settings['seriesOutputDir']

        # class config vars
        self.scanStarted = False
        self.alive = True               # thread status
        self.imageMatrix = None         # matrix that will hold the incoming data
        self.affine = None
        self.tr = None

        # array to keep track of completedVols
        self.completedVols = np.zeros(self.numTimepts, dtype=bool)

        # set up socket server to listen for msgs from pyneal-scanner
        self.context = zmq.Context.instance()
        self.scannerSocket = self.context.socket(zmq.PAIR)
        self.scannerSocket.bind('tcp://{}:{}'.format(self.host, self.scannerPort))
        self.logger.debug('bound to {}:{}'.format(self.host, self.scannerPort))
        self.logger.info('Scan Receiver Server alive and listening....')

        # atexit function, shut down server
        atexit.register(self.killServer)

        # set up socket to communicate with dashboard (if specified)
        if settings['launchDashboard']:
            self.dashboard = True
            self.context = zmq.Context.instance()
            self.dashboardSocket = self.context.socket(zmq.REQ)
            self.dashboardSocket.connect('tcp://127.0.0.1:{}'.format(settings['dashboardPort']))
        else:
            self.dashboard = False

    def run(self):
        # Once this thread is up and running, confirm that the scanner socket
        # is alive and working before proceeding.
        while True:
            print('Waiting for connection from pyneal_scanner')
            msg = self.scannerSocket.recv_string()
            print('Received message: ', msg)
            self.scannerSocket.send_string(msg)
            break
        self.logger.debug('scanner socket connected to Pyneal-Scanner')

        # Start the main loop to listen for new data
        while self.alive:
            # wait for json header to appear. The header is assumed to
            # have key:value pairs for:
            # volIdx - volume index (0-based)
            # dtype - dtype of volume voxel array
            # shape - dims of volume voxel array
            # affine - affine to transform vol to RAS+ mm space
            # TR - repetition time of scan
            volHeader = self.scannerSocket.recv_json(flags=0)
            volIdx = volHeader['volIdx']
            self.logger.debug('received volHeader volIdx {}'.format(volIdx));

            # if this is the first vol, initialize the matrix and store the affine
            if not self.scanStarted:
                self.createImageMatrix(volHeader)
                self.affine = np.array(json.loads(volHeader['affine']))
                self.tr = json.loads(volHeader['TR'])

                self.scanStarted = True     # toggle the scanStarted flag

            # now listen for the image data as a string buffer
            voxelArray = self.scannerSocket.recv(flags=0, copy=False, track=False)

            # format the voxel array according to params from the vol header
            voxelArray = np.frombuffer(voxelArray, dtype=volHeader['dtype'])
            voxelArray = voxelArray.reshape(volHeader['shape'])

            # add the volume to the appropriate location in the image matrix
            self.imageMatrix[:, :, :, volIdx] = voxelArray

            # update the completed volumes table
            self.completedVols[volIdx] = True

            # send response back to Pyneal-Scanner
            response = 'received volIdx {}'.format(volIdx)
            self.scannerSocket.send_string(response)
            self.logger.info(response)

            # update log and dashboard
            self.sendToDashboard(response)

    def createImageMatrix(self, volHeader):
        """ Create empty 4D image matrix

        Once the first volume appears, this function should be called to build
        the empty matrix to store incoming vol data, using info contained in
        the vol header.

        Parameters
        ----------
        volHeader : dict
            dictionary containing header information from the volume, including
            'volIdx', 'dtype', 'shape', and 'affine'

        """
        # create the empty imageMatrix
        self.imageMatrix = np.zeros(shape=(
            volHeader['shape'][0],
            volHeader['shape'][1],
            volHeader['shape'][2],
            self.numTimepts), dtype=volHeader['dtype'])

        self.logger.debug('Image Matrix dims: {}'.format(self.imageMatrix.shape))

    def get_affine(self):
        """ Return the affine for the current series

        """
        return self.affine

    def get_vol(self, volIdx):
        """ Return the requested vol, if it is here.

        Parameters
        ----------
        volIdx : int
            index location (0-based) of the volume you'd like to retrieve

        Returns
        -------
        numpy-array or None
            3D array of voxel data for the requested volume

        """
        if self.completedVols[volIdx]:
            return self.imageMatrix[:, :, :, volIdx]
        else:
            return None

    def get_slice(self, volIdx, sliceIdx):
        """ Return the requested slice, if it is here.

        Parameters
        ----------
        volIdx : int
            index location (0-based) of the volume you'd like to retrieve
        sliceIdx : int
            index location (0-based) of the slice you'd like to retrieve

        Returns
        -------
        numpy-array or None
            2D array of voxel data for the requested slice

        """
        if self.completedVols[volIdx]:
            return self.imageMatrix[:, :, sliceIdx, volIdx]
        else:
            return None

    def sendToDashboard(self, msg):
        """ Send a msg to the Pyneal dashboard

        The dashboard expects messages formatted in specific way, namely a
        dictionary with 2 keys: 'topic', and 'content'. In this case, the
        scan receiver will always use the topic 'pynealScannerLog'.

        The content will be a dictionary with the key 'logString', which has
        the `msg` stored.

        Parameters
        ----------
        msg : string
            log message you want to send to the dashboard

        """
        if self.dashboard:
            dashboardMsg = {'topic': 'pynealScannerLog',
                            'content': {'logString': msg}}
            self.dashboardSocket.send_json(dashboardMsg)
            response = self.dashboardSocket.recv_string()

    def saveResults(self):
        """ Save the numpy 4D image matrix of data as a Nifti File

        Save the image matrix as a Nifti file in the output directory for this
        series

        """
        # build nifti image
        ds = nib.Nifti1Image(self.imageMatrix, self.affine)

        # set the TR appropriately in the header
        pixDims = np.array(ds.header.get_zooms())
        pixDims[3] = self.tr
        ds.header.set_zooms(pixDims)

        # save to disk
        nib.save(ds, join(self.seriesOutputDir, 'receivedFunc.nii.gz'))

    def killServer(self):
        """ Close the thread by setting the alive flag to False """
        self.context.destroy()
        self.alive = False


if __name__ == '__main__':
    # set up settings dict
    settings = {'numTimepts': 100,
                'pynealScannerPort': 5555}

    ### set up logging
    fileLogger = logging.FileHandler('./scanReceiver.log', mode='w')
    fileLogger.setLevel(logging.DEBUG)
    fileLogFormat = logging.Formatter('%(asctime)s - %(levelname)s - %(threadName)s - %(module)s, line: %(lineno)d - %(message)s',
                                      '%m-%d %H:%M:%S')
    fileLogger.setFormatter(fileLogFormat)
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)
    logger.addHandler(fileLogger)

    # start the scanReceiver
    scanReceiver = ScanReceiver(settings)
    scanReceiver.start()
