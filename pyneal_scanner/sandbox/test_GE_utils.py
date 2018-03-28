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
import json
from threading import Thread
from queue import Queue

import numpy as np
import pydicom
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
        self.volCounter = 0

        # parameters we'll build once dicom data starts arriving
        self.firstSliceHasArrived = False
        self.nSlicesPerVol = None
        self.sliceDims = None
        self.nVols = None
        self.pixelSpacing = None

        self.completedSlices = None     # store booleans of which slices have arrived
        self.imageMatrix = None         # 4D image matrix where new slices stored
        self.affine = None              # var to store RAS+ affine, once created
        self.firstSlice_IOP = None      # first slice ImageOrientationPatient tag
        self.firstSlice_IPP = None      # first slice ImagePositionPatient tag
        self.lastSlice_IPP = None       # last slice ImagePositionPatient tag

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
        # if this is the first slice to have arrived, read the dcm header
        # to get relevent information about the series, and to construct
        # the imageMatrix and completedSlices table
        if not self.firstSliceHasArrived:
            self.processFirstSlice(dcm_fname)

        # read in the dicom file
        dcm = pydicom.dcmread(dcm_fname)

        ### Get the Slice Number
        # The dicom tag 'InStackPositionNumber' will tell
        # what slice number within a volume this dicom is.
        # Note: InStackPositionNumber uses one-based indexing,
        # and we want sliceIdx to reflect 0-based indexing
        sliceIdx = getattr(dcm, 'InStackPositionNumber') - 1

        ### Check if you can build the affine using the information that is
        # currently available. We need info from the dicom tags for the first
        # and last slice from any of the 3D volumes
        if self.affine is None and sliceIdx in [0, (self.nSlicesPerVol-1)]:
            if sliceIdx == 0:
                # store the relevent data from the first slice
                self.firstSlice_IOP = np.array(getattr(dcm, 'ImageOrientationPatient'))
                self.firstSlice_IPP = np.array(getattr(dcm, 'ImagePositionPatient'))

            if sliceIdx == (self.nSlicesPerVol-1):
                # store the relevent data from the last slice
                self.lastSlice_IPP = np.array(getattr(dcm, 'ImagePositionPatient'))

            # See if you have valid values for all required parameters for the affine
            if all(x is not None for x in [self.firstSlice_IOP, self.firstSlice_IPP, self.lastSlice_IPP, self.pixelSpacing]):
                self.buildAffine()

        ### Get the volume number
        # We can figure out the volume index using the dicom
        # tags "InstanceNumber" (# out of all images), and
        # the total number of slices.
        # Divide InstanceNumber by ImagesInAcquisition and drop
        # the remainder. Note: InstanceNumber is also one-based index
        volIdx = int(int(getattr(dcm, 'InstanceNumber')-1)/self.nSlicesPerVol)

        ### Place pixel data in imageMatrix
        # transpose the data from numpy standard [row,col] to [col,row]
        self.imageMatrix[:, :, sliceIdx, volIdx] = dcm.pixel_array.T

        # update this slice location in completedSlices
        self.completedSlices[sliceIdx, volIdx] = True

        ### Check if full volume is here, and process if so
        if self.completedSlices[:, self.volCounter].all():
            self.processVolume(self.volCounter)

            # increment volCounter
            self.volCounter += 1
            if self.volCounter >= self.nVols:
                self.stop()


    def processFirstSlice(self, dcm_fname):
        """
        Read the dicom header from the supplied slice to get relevant info
        that pertains to the whole scan series. Build the imageMatrix and
        completedSlice table to store subsequent slice data as it arrives
        """
        # Read the header dicom tags only
        dcmHdr = pydicom.dcmread(dcm_fname, stop_before_pixels=True)

        ### Get series parameters from the dicom tags
        self.nSlicesPerVol = getattr(dcmHdr, 'ImagesInAcquisition')
        self.nVols = getattr(dcmHdr, 'NumberOfTemporalPositions')
        self.pixelSpacing = getattr(dcmHdr, 'PixelSpacing')

        # Note: [cols, rows] to match the order of the transposed pixel_array later on
        self.sliceDims = np.array([getattr(dcmHdr, 'Columns'),
                                    getattr(dcmHdr, 'Rows')])


        ### Build the image matrix and completed slices table
        self.imageMatrix = np.zeros(shape=(self.sliceDims[0],
                                        self.sliceDims[1],
                                        self.nSlicesPerVol,
                                        self.nVols), dtype=np.uint16)
        self.completedSlices = np.zeros(shape=(self.nSlicesPerVol,
                                            self.nVols), dtype=bool)

        ### Update the flow control flag
        self.firstSliceHasArrived = True


    def buildAffine(self):
        """
        Build the affine matrix that will transform the data to RAS+.

        This function should only be called once the required data has been
        extracted from the dicom tags from the relevant slices. The affine matrix
        is constructed by using the information in the ImageOrientationPatient
        and ImagePositionPatient tags from the first and last slices in a volume.

        However, note that those tags will tell you how to orient the image to
        DICOM reference coordinate space, which is LPS+. In order to to get to
        RAS+ we have to invert the first two axes.

        More info on building this affine at:
        http://nipy.org/nibabel/dicom/dicom_orientation.html &
        http://nipy.org/nibabel/coordinate_systems.html
        """
        ### Get the ImageOrientation values from the first slice,
        # split the row-axis values (0:3) and col-axis values (3:6)
        # and then invert the first and second values of each
        rowAxis_orient = self.firstSlice_IOP[0:3] * np.array([-1, -1, 1])
        colAxis_orient = self.firstSlice_IOP[3:6] * np.array([-1, -1, 1])

        ### Get the voxel size along Row and Col axis
        voxSize_row = float(self.pixelSpacing[0])
        voxSize_col = float(self.pixelSpacing[1])

        ### Figure out the change along the 3rd axis by subtracting the
        # ImagePosition of the last slice from the ImagePosition of the first,
        # then dividing by 1/(total number of slices-1), then invert to
        # make it go from LPS+ to RAS+
        slAxis_orient = (self.firstSlice_IPP - self.lastSlice_IPP) / (1-self.nSlicesPerVol)
        slAxis_orient = slAxis_orient * np.array([-1, -1, 1])

        ### Invert the first two values of the firstSlice ImagePositionPatient.
        # This tag represents the translation needed to take the origin of our 3D voxel
        # array to the origin of the LPS+ reference coordinate system. Since we want
        # RAS+, need to invert those first two axes
        voxTranslations = self.firstSlice_IPP * np.array([-1, -1, 1])

        ### Assemble the affine matrix
        self.affine = np.matrix([
            [rowAxis_orient[0] * voxSize_row,  colAxis_orient[0] * voxSize_col, slAxis_orient[0], voxTranslations[0]],
            [rowAxis_orient[1] * voxSize_row,  colAxis_orient[1] * voxSize_col, slAxis_orient[1], voxTranslations[1]],
            [rowAxis_orient[2] * voxSize_row,  colAxis_orient[2] * voxSize_col, slAxis_orient[2], voxTranslations[2]],
            [0, 0, 0, 1]
            ])

    def processVolume(self, volIdx):
        """
        Extract the 3D numpy array of voxel data for the current volume (set by
        self.volCounter attribute). Reorder the voxel data so that it is RAS+,
        build a header JSON object, and then send both the header and the voxel
        data out over the socket connection to Pyneal
        """
        print('Volume {} arrived'.format(volIdx))

        ### Prep the voxel data by extracting this vol from the imageMatrix,
        # and then converting to a Nifti1 object in order to set the voxel
        # order to RAS+, then get the voxel data as contiguous numpy array
        thisVol = self.imageMatrix[:,:,:,volIdx]
        thisVol_nii = nib.Nifti1Image(thisVol, self.affine)
        thisVol_RAS = nib.as_closest_canonical(thisVol_nii)     # make RAS+
        thisVol_RAS_data = np.ascontiguousarray(thisVol_RAS.get_data())


        ### Create a header with metadata info
        volHeader = {
            'volIdx':volIdx,
            'dtype':str(thisVol_RAS_data.dtype),
            'shape':thisVol_RAS_data.shape,
            'affine':json.dumps(thisVol_RAS.affine.tolist())
            }

        ### Send the voxel array and header to the scannerSocket
        self.sendVolToScannerSocket(volHeader, thisVol_RAS_data)


    def sendVolToScannerSocket(self, volHeader, voxelArray):
        """
        Send the volume data over the scannerSocket.
            - 'volHeader' is expected to be a dictionary with key:value
            pairs for relevant metadata like 'volIdx' and 'affine'
            - 'voxelArray' is expected to be a 3D numpy array of voxel
            data from the volume reoriented to RAS+
        """
        self.logger.debug('TO scannerSocket: vol {}'.format(volHeader['volIdx']))

        ### Send data out the socket, listen for response
        self.scannerSocket.send_json(volHeader, zmq.SNDMORE) # header as json
        self.scannerSocket.send(voxelArray, flags=0, copy=False, track=False)
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

    # wait for remote to connect on scannerSocket
    logger.info('Waiting for connection on scannerSocket...')
    while True:
        scannerSocket.send_string('hello')
        msg = scannerSocket.recv_string()
        if msg == 'hello':
            break
    logger.info('scannerSocket connected')

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
