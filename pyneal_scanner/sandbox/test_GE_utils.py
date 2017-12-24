"""
Set of utilities for testing out new features
"""
from __future__ import print_function
from __future__ import division

import os
from os.path import join
import sys
import time
import re
import logging
from threading import Thread
from queue import Queue

import numpy as np
import dicom
import nibabel as nib
import argparse
import zmq

# default path to where new series directories
# will appear (e.g. [baseDir]/p###/e###/s###)
GE_default_baseDir = '/export/home1/sdc_image_pool/images'

class test_GE_processSlice(Thread):
    """
    Class to process each dicom slice in the dicom queue. This class is
    designed to run in a separate thread. While running, it will pull slice file
    names off of the dicomQ and process each slice.

    Processing each slice will include reading the dicom file and extracting
    the pixel array and any relevant header information. The pixel array from
    each slice will be stored in an 4d image matrix. Whenever all of the slices
    from a single volume have arrived, that volume will be reformatted
    so that its axes correspond to RAS+. The volume, along with a JSON header
    containing metadata on that volume, will be sent out over the socket connection
    """
    def __init__(self, dicomQ, scannerSocket, interval=.2):
        # start the thread upon creation
        Thread.__init__(self)

        # set up logger
        self.logger = logging.getLogger(__name__)

        # initialize class parameters
        self.dicomQ = dicomQ
        self.interval = interval
        self.alive = True
        self.scannerSocket = scannerSocket
        self.totalProcessed = 0             # counter for total number of slices processed
        self.nSlicesPerVol = None           # once set, won't need to be retrieved each time

        self.imageMatrix = None         # init var to store imageMatrix in
        self.completedSlices = None     # table to store booleans indicating which slices have arrived
        self.volCounter = 0
        self.affine = None              # init var to store RAS+ affine in



    def run(self):
        self.logger.debug('GE_processSlice thread started')

        # function to run on loop
        while self.alive:

            # if there are any slices in the queue, process them
            if not self.dicomQ.empty():
                numSlicesInQueue = self.dicomQ.qsize()

                # loop through all slices currently in queue & process
                for s in range(numSlicesInQueue):
                    dcm_fname = self.dicomQ.get(True, 2)    # retrieve the filename from the queue

                    # process this slice
                    self.processDcmSlice(dcm_fname)

                    # complete this task, thereby clearing it from the queue
                    self.dicomQ.task_done()

                # log how many were processed
                self.totalProcessed += numSlicesInQueue
                self.logger.debug('Processed {} tasks from the queue ({} total)'.format(numSlicesInQueue, self.totalProcessed))

            # pause for a bit
            time.sleep(self.interval)


    def processDcmSlice(self, dcm_fname):
        """
        read the slice dicom. Format the data and header.
        Send data and header out over the socket connection
        """
        # read in the dicom file
        dcm = dicom.read_file(dcm_fname)

        # The tag 'ImagesInAcquisition' stores the total number of
        # slices for every volume. Setting this as a class attribute
        # means it does not have to be retrieved, redundantly, when
        # processing each slice.
        if self.nSlicesPerVol is None:
            self.nSlicesPerVol = getattr(dcm, 'ImagesInAcquisition')

        ### Get the Slice Number
        # The dicom tag 'InStackPositionNumber' will tell
        # what slice number within a volume this dicom is.
        # Note: InStackPositionNumber uses one-based indexing,
        # and we want sliceIdx to reflect 0-based indexing
        sliceIdx = getattr(dcm, 'InStackPositionNumber') - 1
        #print('this slice idx: {}'.format(sliceIdx))

        ### Get the volume number
        # We can figure out the volume index using the dicom
        # tags "InstanceNumber" (# out of all images), and
        # the total number of slices.
        # Divide InstanceNumber by ImagesInAcquisition and drop
        # the remainder. Note: InstanceNumber is also one-based index
        volIdx = int(int(getattr(dcm, 'InstanceNumber')-1)/self.nSlicesPerVol)

        ### Update completed slices
        self.updateCompletedSlices(sliceIdx, int(volIdx))

        ### TESTING
        #print(self.volCounter)
        #print(self.completedSlices[:,self.volCounter])
        if self.completedSlices[:,self.volCounter].all():
            print('Volume {} arrived'.format(self.volCounter))
            self.volCounter += 1




        #
        #
        #
        # # create a header with metadata info
        # sliceHeader = {
        #     'sliceIdx':sliceIdx,
        #     'volIdx':volIdx,
        #     'nSlicesPerVol':self.nSlicesPerVol,
        #     'dtype':str(pixel_array.dtype),
        #     'shape':pixel_array.shape,
        #     }
        #
        # ### Send the pixel array and header to the scannerSocket
        # self.sendSliceToScannerSocket(sliceHeader, pixel_array)

    def updateCompletedSlices(self, sliceIdx, volIdx):
        """
        Update the completed slices array
        """
        if self.completedSlices is None:
            # initialize completedSlices array. nSlicesPerVol has to be set
            # already. Since no way to no total volume number from DICOM, set
            # it to an absurdly large value (2000 vols @ 1s TR = 30 min run)
            self.completedSlices = np.zeros(shape=(self.nSlicesPerVol, 2000),
                                            dtype=bool)

        # update the table with the current slice
        self.completedSlices[sliceIdx, volIdx] = True
        print('{}, {}'.format(sliceIdx, volIdx))


    def sendSliceToScannerSocket(self, sliceHeader, slicePixelArray):
        """
        Send the dicom slice over the scannerSocket.
            - 'sliceHeader' is expected to be a dictionary with key:value
            pairs for relevant slice metadata like 'sliceIdx', and 'volIdx'
            - 'slicePixelArray' is expected to be a 2D numpy array of pixel
            data from the slice reoriented to RAS+
        """
        self.logger.debug('TO scannerSocket: vol {}, slice {}'.format(sliceHeader['volIdx'], sliceHeader['sliceIdx']))

        ### Send data out the socket, listen for response
        self.scannerSocket.send_json(sliceHeader, zmq.SNDMORE) # header as json
        self.scannerSocket.send(slicePixelArray, flags=0, copy=False, track=False)
        scannerSocketResponse = self.scannerSocket.recv_string()

        # log the success
        self.logger.debug('FROM scannerSocket: {}'.format(scannerSocketResponse))


    def stop(self):
        # function to stop the Thread
        self.alive = False


class test_GE_monitorSeriesDir(Thread):
    """
    Class to monitor for new slices images to appear in the seriesDir.
    This class will run indpendently in a separate thread.
    Each new dicom file that appears will be added to the Queue
    for further processing
    """
    def __init__(self, seriesDir, dicomQ, interval=.2):
        # start the thead upon creation
        Thread.__init__(self)

        # set up logger
        self.logger = logging.getLogger(__name__)

        # initialize class parameters
        self.interval = interval            # interval for polling for new files (s)
        self.seriesDir = seriesDir          # full path to series directory
        self.dicomQ = dicomQ                # queue to store dicom files
        self.alive = True                   # thread status
        self.numSlicesAdded = 0             # counter to keep track of # of slices added overall
        self.queued_dicom_files = set()     # empty set to store names of files placed on queue


    def run(self):
        # function that loops while the Thead is still alive
        while self.alive:

            # create a set of all dicoms currently in the series directory
            currentDicoms = set(os.listdir(self.seriesDir))

            # grab only the the dicoms which haven't already been added to the queue
            newDicoms = [f for f in currentDicoms if f not in self.queued_dicom_files]

            # loop over each of the newDicoms and add them to queue
            for f in newDicoms:
                dicom_fname = join(self.seriesDir, f)
                try:
                    self.dicomQ.put(dicom_fname)
                except:
                    self.logger.error('failed on: {}'.format(dicom_fname))
                    print(sys.exc_info())
                    sys.exit()
            if len(newDicoms) > 0:
                self.logger.debug('Put {} new slices on the queue'.format(len(newDicoms)))
            self.numSlicesAdded += len(newDicoms)

            # now update the set of dicoms added to the queue
            self.queued_dicom_files.update(set(newDicoms))

            # pause
            time.sleep(self.interval)


    def get_numSlicesAdded(self):
        return self.numSlicesAdded


    def stop(self):
        # function to stop the Thread
        self.alive = False






def test_GE_launch_rtfMRI(scannerSettings, scannerDirs):
    """
    launch a real-time session in a GE environment. This should be called
    from pynealScanner.py before starting the scanner. Once called, this
    method will take care of:
        - monitoring the sessionDir for a new series directory to appear (and
        then returing the name of the new series dir)
        - set up the socket connection to send slice data over
        - creating a Queue to store newly arriving DICOM files
        - start a separate thread to monitor the new seriesDir
        - start a separate thread to process DICOMs that are in the Queue
    """
    # Create a reference to the logger. This assumes the logger has already
    # been created and customized by pynealScanner.py
    logger = logging.getLogger(__name__)

    #### SET UP SCANNERSOCKET (this is what we'll use to
    #### send data (e.g. header, slice pixel data) to remote connections)
    # figure out host and port number to use
    host = scannerSettings.get_scannerSocketHost()
    port = scannerSettings.get_scannerSocketPort()
    logger.debug('Scanner Socket Host: {}'.format(host))
    logger.debug('Scanner Socket Port: {}'.format(port))

    # create a socket connection
    from utils.general_utils import create_scannerSocket
    scannerSocket = create_scannerSocket(host, port)
    logger.debug('Created scannerSocket')
    #
    # # wait for remote to connect on scannerSocket
    # logger.info('Waiting for connection on scannerSocket...')
    # while True:
    #     scannerSocket.send_string('hello')
    #     msg = scannerSocket.recv_string()
    #     if msg == 'hello':
    #         break
    # logger.info('scannerSocket connected')

    ### Wait for a new series directory appear
    logger.info('Waiting for new seriesDir...')
    seriesDir = scannerDirs.waitForSeriesDir()
    logger.info('New Series Directory: {}'.format(seriesDir))

    ### Start threads to A) watch for new slices, and B) process
    # slices as they appear
    # initialize the dicom queue to keep store newly arrived
    # dicom slices, and keep track of which have been processed
    dicomQ = Queue()

    # create instance of class that will monitor seriesDir. Pass in
    # a copy of the dicom queue. Start the thread going
    scanWatcher = test_GE_monitorSeriesDir(seriesDir, dicomQ)
    scanWatcher.start()

    # create an instance of the class that will grab slice dicoms
    # from the queue, reformat the data, and pass over the socket
    # to pyneal. Start the thread going
    sliceProcessor = test_GE_processSlice(dicomQ, scannerSocket)
    sliceProcessor.start()
