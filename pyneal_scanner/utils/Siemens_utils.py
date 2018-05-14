"""
Set of classes and methods specific to Siemens scanning environments
"""
from __future__ import print_function
from __future__ import division

import os
from os.path import join
import sys
import time
import re
import json
import glob
import logging
from threading import Thread
from queue import Queue

import numpy as np
import pydicom
import nibabel as nib
from nibabel.nicom import dicomreaders
import argparse
import zmq

# regEx for Siemens style file naming
Siemens_filePattern = re.compile('\d{3}_\d{6}_\d{6}.dcm')

# regEx for pulling the volume field out of the mosaic file name
Siemens_mosaicVolumeNumberField = re.compile('(?<=\d{6}_)\d{6}')
Siemens_mosaicSeriesNumberField = re.compile('(?<=\d{3}_)\d{6}(?=_\d{6}.dcm)')


class Siemens_DirStructure():
    """
    Methods for finding and returning the names and paths of series files
    in a Siemens Scanning Environment
    """

    def __init__(self, scannerSettings):
        # initialize class attributes
        if 'scannerBaseDir' in scannerSettings.allSettings:
            self.baseDir = scannerSettings.allSettings['scannerBaseDir']
        else:
            print('No scannerBaseDir found in scannerConfig file')
            sys.exit()

        self.sessionDir = self.baseDir


    def print_currentSeries(self):
        """
        Find all of the series present in given sessionDir, and print them
        all, along with time since last modification, and directory size
        """
        # find the sessionDir, if not already found
        if self.sessionDir is None:
            self.findSessionDir()
        print('Session Dir: ')
        print('{}'.format(self.sessionDir))

        # find all mosaic files in the sessionDir
        self.uniqueSeries = self.getUniqueSeries()
        if len(self.uniqueSeries) == 0:
            print('No mosaic files found in {}'.format(self.sessionDir))
        else:
            # print out info on each unique series in sessionDir
            currentTime = int(time.time())
            print('Unique Series: ')
            for series in sorted(self.uniqueSeries):
                # get list of all dicoms that match this series number
                thisSeriesDicoms = glob.glob(join(self.sessionDir, ('*_' + series + '_*.dcm')))

                # get time since last modification for last dicom in list
                lastModifiedTime = os.stat(thisSeriesDicoms[-1]).st_mtime
                timeElapsed = currentTime - lastModifiedTime
                m,s = divmod(timeElapsed,60)
                time_string = '{} min, {} s ago'.format(int(m),int(s))

                print('    {}\t{} files \t{}'.format(series, len(thisSeriesDicoms), time_string))


    def getUniqueSeries(self):
        """
        return a list of unique series numbers from the filenames of the files
        found in the sessionDir
        """
        uniqueSeries = []
        self.allMosaics = [f for f in os.listdir(self.sessionDir) if Siemens_filePattern.match(f)]
        if len(self.allMosaics) > 0:
            # find unique series numbers among all mosaics
            seriesNums = []
            for f in self.allMosaics:
                seriesNums.append(Siemens_mosaicSeriesNumberField.search(f).group())
            uniqueSeries = set(seriesNums)

        return uniqueSeries


    def waitForNewSeries(self, interval=.1):
        """
        listen for the arrival of new series images.
        Once a scan starts, new series mosaic files will be created
        in the sessionDir. By the time this function is called, this
        class should already have the sessionDir defined
        """
        startTime = int(time.time())    # tag the start time
        keepWaiting = True

        existingSeries = self.getUniqueSeries()

        while keepWaiting:
            # get all of the unique series again
            currentSeries = self.getUniqueSeries()

            # compare against existing series
            diff = currentSeries - existingSeries
            if len(diff) > 0:
                newSeries = diff.pop()
                keepWaiting = False

            # pause before searching directories again
            time.sleep(interval)

        # return the found series directory
        return newSeries


class Siemens_BuildNifti():
    """
    Build a 3D or 4D Nifti image from all of the dicom mosaic images in a
    directory.

    Input is a path to a series directory containing dicom mosaic images. Image
    parameters, like voxel spacing and dimensions, are obtained automatically
    from the info in the dicom tags

    Output is a Nifti1 formatted 3D (anat) or 4D (func) file in RAS+ orientation
    """
    def __init__(self, seriesDir, seriesNum):
        """
        Initialize class:
            - seriesDir: the path to directory containing all dicom files. Note
                that for Siemens, this dir can contain multiple series
            - seriesNum: the seriesNum of the dicoms you want to use to build file
        """
        # initialize attributes
        self.seriesDir = seriesDir
        self.seriesNum = seriesNum
        self.niftiImage = None

        # make a list of the specified raw dicom mosaic files in this dir
        rawDicoms = glob.glob(join(self.seriesDir, ('*_' + str(self.seriesNum).zfill(6) + '_*.dcm')))

        # figure out what type of image this is, 4d or 3d
        self.scanType = self._determineScanType(rawDicoms[0])

        # build the nifti image
        if self.scanType == 'anat':
            self.niftiImage = self.buildAnat(rawDicoms)
        elif self.scanType == 'func':
            self.niftiImage = self.buildFunc(rawDicoms)


    def buildAnat(self, dicomFiles):
        """
        Given a list of dicomFiles, build a 3D anatomical image from them.
        Figure out the image dimensions and affine transformation to map
        from voxels to mm from the dicom tags
        """
        # read the first dicom in the list to get overall image dimensions
        dcm = pydicom.dcmread(join(self.seriesDir, dicomFiles[0]), stop_before_pixels=1)
        sliceDims = (getattr(dcm, 'Columns'), getattr(dcm, 'Rows'))
        self.nSlicesPerVol = len(dicomFiles)
        sliceThickness = getattr(dcm, 'SliceThickness')
        voxSize = getattr(dcm, 'PixelSpacing')

        ### Build 3D array of voxel data
        # create an empty array to store the slice data
        imageMatrix = np.zeros(shape=(
                                sliceDims[0],
                                sliceDims[1],
                                self.nSlicesPerVol),
                                dtype='int16')

        # Use the InstanceNumber tag to order the slices. This works for anat
        # 3D images only, since the instance numbers do not repeat as they would
        # with functional data with multiple volumes
        sliceDict = {}
        for s in dicomFiles:
            dcm = pydicom.dcmread(join(self.seriesDir, s))
            sliceDict[dcm.InstanceNumber] = join(self.seriesDir, s)

        # sort by InStackPositionNumber and assemble the image
        for sliceIdx,ISPN in enumerate(sorted(sliceDict.keys())):
            dcm = pydicom.dcmread(sliceDict[ISPN])

            # grab the slices necessary for creating the affine transformation
            if sliceIdx == 0:
                firstSliceDcm = dcm
            if sliceIdx == self.nSlicesPerVol-1:
                lastSliceDcm = dcm

            # extract the pixel data as a numpy array. Transpose
            # so that the axes order go [cols, rows]
            pixel_array = dcm.pixel_array.T

            # place in the image matrix
            imageMatrix[:, :, sliceIdx] = pixel_array

        ### create the affine transformation to map from vox to mm space
        # in order to do this, we need to get some values from the first and
        # last slices in the volume.
        firstSlice = sliceDict[sorted(sliceDict.keys())[0]]
        lastSlice = sliceDict[sorted(sliceDict.keys())[-1]]

        dcm_first = pydicom.dcmread(firstSlice)
        dcm_last = pydicom.dcmread(lastSlice)
        self.pixelSpacing = getattr(dcm_first, 'PixelSpacing')
        self.firstSlice_IOP = np.array(getattr(dcm_first, 'ImageOrientationPatient'))
        self.firstSlice_IPP = np.array(getattr(dcm_first, 'ImagePositionPatient'))
        self.lastSlice_IPP = np.array(getattr(dcm_last, 'ImagePositionPatient'))

        # now we can build the affine
        affine = self.buildAffine()

        ### Build a Nifti object, reorder it to RAS+
        anatImage = nib.Nifti1Image(imageMatrix, affine=affine)
        anatImage_RAS = nib.as_closest_canonical(anatImage)     # reoder to RAS+
        print('Nifti image dims: {}'.format(anatImage_RAS.shape))

        return anatImage_RAS


    def buildFunc(self, dicomFiles):
        """
        Given a list of dicomFile paths, build a 4d functional image. For
        Siemens scanners, each dicom file is assumed to represent a mosaic
        image comprised of mulitple slices. This tool will split apart the
        mosaic images, and construct a 4D nifti object. The 4D nifti object
        contain a voxel array ordered like RAS+ as well the affine transformation
        to map between vox and mm space
        """
        imageMatrix = None
        affine = None

        # make dicomFiles store the full path
        dicomFiles = [join(self.seriesDir, f) for f in dicomFiles]

        ### Loop over all dicom mosaic files
        nVols = len(dicomFiles)
        for mosaic_dcm_fname in dicomFiles:
            ### Parse the mosaic image into a 3D volume
            # we use the nibabel mosaic_to_nii() method which does a lot of the
            # heavy-lifting of extracting slices, arranging in a 3D array, and grabbing
            # the affine
            dcm = pydicom.dcmread(mosaic_dcm_fname)     # create dicom object

            # for mosaic files, the instanceNumber tag will correspond to the
            # volume number (using a 1-based indexing, so subtract by 1)
            volIdx = dcm.InstanceNumber - 1

            # convert the dicom object to nii
            thisVol = dicomreaders.mosaic_to_nii(dcm)

            # convert to RAS+
            thisVol_RAS = nib.as_closest_canonical(thisVol)

            # construct the imageMatrix if it hasn't been made yet
            if imageMatrix is None:
                imageMatrix = np.zeros(shape=(thisVol_RAS.shape[0],
                                            thisVol_RAS.shape[1],
                                            thisVol_RAS.shape[2],
                                            nVols), dtype=np.uint16)

            # construct the affine if it isn't made yet
            if affine is None:
                affine = thisVol_RAS.affine

            # Add this data to the image matrix
            imageMatrix[:, :, :, volIdx] = thisVol_RAS.get_data()

        ### Build a Nifti object
        funcImage = nib.Nifti1Image(imageMatrix, affine=affine)

        return funcImage


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
        affine = np.matrix([
            [rowAxis_orient[0] * voxSize_row,  colAxis_orient[0] * voxSize_col, slAxis_orient[0], voxTranslations[0]],
            [rowAxis_orient[1] * voxSize_row,  colAxis_orient[1] * voxSize_col, slAxis_orient[1], voxTranslations[1]],
            [rowAxis_orient[2] * voxSize_row,  colAxis_orient[2] * voxSize_col, slAxis_orient[2], voxTranslations[2]],
            [0, 0, 0, 1]
            ])

        return affine


    def _determineScanType(self, dicomFile):
        """
        Figure out what type of scan this is, single 3D volume (anat), or
        a 4D dataset built up of 2D slices (func) based on info found
        in the dicom tags
        """
        # read the dicom file
        dcm = pydicom.dcmread(join(self.seriesDir, dicomFile), stop_before_pixels=1)

        if getattr(dcm,'MRAcquisitionType') == '3D':
            scanType = 'anat'
        elif getattr(dcm, 'MRAcquisitionType') == '2D':
            scanType = 'func'
        else:
            print('Cannot determine a scan type from this image!')
            sys.exit()

        return scanType


    def get_scanType(self):
        """ Return the scan type """
        return self.scanType


    def get_niftiImage(self):
        """ Return the constructed Nifti Image """
        return self.niftiImage


    def write_nifti(self, output_path):
        """
        write the nifti file to disk using the abs path
        specified by output_fName
        """
        nib.save(self.niftiImage, output_path)
        print('Image saved at: {}'.format(output_path))


class Siemens_monitorSessionDir(Thread):
    """
    Class to monitor for new mosaic images to appear in the sessionDir. This
    class will run independently in a separate thread. Each new mosaic file
    that appears and matches the current series number will be added to the
    Queue for further processing
    """
    def __init__(self, sessionDir, seriesNum, dicomQ, interval=.5):
        # start the thread upon completion
        Thread.__init__(self)

        # set up logger
        self.logger = logging.getLogger(__name__)

        # initialize class parameters
        self.interval = interval            # interval for polling for new files
        self.sessionDir = sessionDir        # full path to series directory
        self.seriesNum = seriesNum          # series number of current series
        self.dicomQ = dicomQ                # queue to store dicom mosaic files
        self.alive = True                   # thread status
        self.numMosaicsAdded = 0            # counter to keep track of # mosaics
        self.queued_mosaic_files = set()    # empty set to store names of queued mosaic


    def run(self):
        # function that runs while the Thread is still alive
        while self.alive:

            # create a set of all mosaic files with the current series num
            #currentMosaics = set(os.listdir(self.seriesDir))
            currentMosaics = set(glob.glob(join(self.sessionDir, ('*_' + str(self.seriesNum).zfill(6) + '_*.dcm'))))

            # grab only the ones that haven't already been added to the queue
            newMosaics = [f for f in currentMosaics if f not in self.queued_mosaic_files]

            # loop over each of the new mosaic files, add each to queue
            for f in newMosaics:
                mosaic_fname = join(self.sessionDir, f)
                try:
                    self.dicomQ.put(mosaic_fname)
                except:
                    self.logger.error('failed on: {}'.format(mosaic_fname))
                    print(sys.exc_info())
                    sys.exit()
            if len(newMosaics) > 0:
                self.logger.debug('Put {} new mosaic file on the queue'.format(len(newMosaics)))
            self.numMosaicsAdded += len(newMosaics)

            # now update the set of mosaics added to the queue
            self.queued_mosaic_files.update(set(newMosaics))

            # pause
            time.sleep(self.interval)


    def get_numMosaicsAdded(self):
        return self.numMosaicsAdded


    def stop(self):
        # function to stop the thread
        self.alive = False


class Siemens_processMosaic(Thread):
    """
    Class to process each mosaic file in the queue. This class will run in a
    separate thread. While running, it will pull 'tasks' off of the queue and
    process each one. Processing each task involves reading the mosaic file,
    converting it to a 3D Nifti object, reordering it to RAS+, and then sending
    the volume out over the pynealSocket
    """
    def __init__(self, dicomQ, pynealSocket, interval=.2):
        # start the threat upon creation
        Thread.__init__(self)

        # set up logger
        self.logger = logging.getLogger(__name__)

        # initialize class parameters
        self.dicomQ = dicomQ
        self.interval = interval        # interval between polling queue for new files
        self.alive = True
        self.pynealSocket = pynealSocket
        self.totalProcessed = 0         # counter for total number of slices processed


    def run(self):
        self.logger.debug('Siemens_processMosaic started')

        # function to run on loop
        while self.alive:

            # if there are any mosaic files in the queue, process them
            if not self.dicomQ.empty():
                numMosaicsInQueue = self.dicomQ.qsize()

                # loop through all mosaics currently in queue & process
                for m in range(numMosaicsInQueue):
                    # retrieve file name from queue
                    mosaic_dcm_fname = self.dicomQ.get(True, 2)

                    # ensure the file has copied completely
                    file_size = 0
                    while True:
                        file_info = os.stat(mosaic_dcm_fname)
                        if file_info.st_size == 0 or file_info.st_size > file_size:
                            file_size = file_info.st_size
                        else:
                            break

                    # process this mosaic
                    self.processMosaicFile(mosaic_dcm_fname)

                    # complete this task, thereby clearing it from the queue
                    self.dicomQ.task_done()

                # log how many were processed
                self.totalProcessed += numMosaicsInQueue
                self.logger.debug('Processed {} tasks from the queue ({} total)'.format(numMosaicsInQueue, self.totalProcessed))

            # pause for a bit
            time.sleep(self.interval)


    def processMosaicFile(self, mosaic_dcm_fname):
        """
        Read the dicom mosaic file. Convert to a nifti object that will
        provide the 3D voxel array for this mosaic. Reorder to RAS+, and
        then send to the pynealSocket

        mosaic_dcm_fname: full path to the mosaic file
        """
        ### Figure out the volume index for this mosaic by reading
        # the field from the file name itself
        mosaicFile_root, mosaicFile_name = os.path.split(mosaic_dcm_fname)
        volIdx = int(Siemens_mosaicVolumeNumberField.search(mosaicFile_name).group(0))-1
        self.logger.info('Volume {} processing'.format(volIdx))


        ### Parse the mosaic image into a 3D volume
        # we use the nibabel mosaic_to_nii() method which does a lot of the
        # heavy-lifting of extracting slices, arranging in a 3D array, and grabbing
        # the affine
        dcm = pydicom.dcmread(mosaic_dcm_fname)     # create dicom object
        thisVol = dicomreaders.mosaic_to_nii(dcm)   # convert to nifti

        # convert to RAS+
        thisVol_RAS = nib.as_closest_canonical(thisVol)

        # get the data as a contiguous array (required for ZMQ)
        thisVol_RAS_data = np.ascontiguousarray(thisVol_RAS.get_data())

        ### Create a header with metadata info
        volHeader = {
            'volIdx':volIdx,
            'dtype':str(thisVol_RAS_data.dtype),
            'shape':thisVol_RAS_data.shape,
            'affine':json.dumps(thisVol_RAS.affine.tolist())
            }

        ### Send the voxel array and header to the pynealSocket
        self.sendVolToPynealSocket(volHeader, thisVol_RAS_data)


    def sendVolToPynealSocket(self, volHeader, voxelArray):
        """
        Send the volume data over the pynealSocket.
            - 'volHeader' is expected to be a dictionary with key:value
            pairs for relevant metadata like 'volIdx' and 'affine'
            - 'voxelArray' is expected to be a 3D numpy array of voxel
            data from the volume reoriented to RAS+
        """
        self.logger.debug('TO pynealSocket: vol {}'.format(volHeader['volIdx']))

        ### Send data out the socket, listen for response
        self.pynealSocket.send_json(volHeader, zmq.SNDMORE) # header as json
        self.pynealSocket.send(voxelArray, flags=0, copy=False, track=False)
        pynealSocketResponse = self.pynealSocket.recv_string()

        # log the success
        self.logger.debug('FROM pynealSocket: {}'.format(pynealSocketResponse))

        # check if that was the last volume, and if so, stop
        if 'STOP' in pynealSocketResponse:
            self.stop()

    def stop(self):
        # function to stop the Thread
        self.alive = False


def Siemens_launch_rtfMRI(scannerSettings, scannerDirs):
    """
    launch a real-time session in a Siemens environment. This should be called
    from pynealScanner.py before starting the scanner. Once called, this
    method will take care of:
        - monitoring the sessionDir for new series files to appear (and
        then returing the new series number)
        - set up the socket connection to send volume data over
        - creating a Queue to store newly arriving DICOM files
        - start a separate thread to monitor the new series appearing
        - start a separate thread to process DICOMs that are in the Queue
    """
    # Create a reference to the logger. This assumes the logger has already
    # been created and customized by pynealScanner.py
    logger = logging.getLogger(__name__)

    #### SET UP PYNEAL SOCKET (this is what we'll use to
    #### send data (e.g. header, volume voxel data) to remote connections)
    # figure out host and port number to use
    host = scannerSettings.get_pynealSocketHost()
    port = scannerSettings.get_pynealSocketPort()
    logger.debug('Scanner Socket Host: {}'.format(host))
    logger.debug('Scanner Socket Port: {}'.format(port))

    # create a socket connection
    from .general_utils import create_pynealSocket
    pynealSocket = create_pynealSocket(host, port)
    logger.debug('Created pynealSocket')

    # wait for remote to connect on pynealSocket
    logger.info('Connecting to pynealSocket...')
    while True:
        msg = 'hello from pyneal_scanner '
        pynealSocket.send_string(msg)
        msgResponse = pynealSocket.recv_string()
        if msgResponse == msg:
            break
    logger.info('pynealSocket connected')

    ### Wait for a new series directory appear
    logger.info('Waiting for new series files to appear...')
    seriesNum = scannerDirs.waitForNewSeries()
    logger.info('New Series Number: {}'.format(seriesNum))

    ### Start threads to A) watch for new mosaic files, and B) process
    # them as they appear
    # initialize the dicom queue to keep store newly arrived
    # dicom mosaic images, and keep track of which have been processed
    dicomQ = Queue()

    # create instance of class that will monitor sessionDir for new mosaic
    # images to appear. Pass in a copy of the dicom queue. Start the thread
    scanWatcher = Siemens_monitorSessionDir(scannerDirs.sessionDir, seriesNum, dicomQ)
    scanWatcher.start()

    # create an instance of the class that will grab mosaic dicoms
    # from the queue, reformat the data, and pass over the socket
    # to pyneal. Start the thread going
    mosaicProcessor = Siemens_processMosaic(dicomQ, pynealSocket)
    mosaicProcessor.start()
