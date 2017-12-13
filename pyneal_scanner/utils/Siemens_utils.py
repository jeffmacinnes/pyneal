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
import logging
from threading import Thread
from queue import Queue

import numpy as np
import dicom
import nibabel as nib
import argparse
import zmq

# regEx for Siemens style file naming
Siemens_filePattern = re.compile('RESEARCH.*.MR.PRISMA_HEAD.*')

# regEx for pulling the volume field out of the mosaic file name
Siemens_mosaicVolumeNumberField = re.compile('(?<=HEAD\.\d{4}\.)\d{4}')


class Siemens_DirStructure():
    """
    Methods for finding and returning the names and paths of series directories
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


    def print_seriesDirs(self):
        """
        Find all of the series dirs in given sessionDir, and print them
        all, along with time since last modification, and directory size
        """
        # find the sessionDir, if not already found
        if self.sessionDir is None:
            self.findSessionDir()

        # get a list of all series dirs in the sessionDir
        seriesDirs = self._findAllSubdirs(self.sessionDir)

        if seriesDirs is not None:
            # sort based on modification time
            seriesDirs = sorted(seriesDirs, key=lambda x: x[1])

            # print directory info to the screen
            print('Session Dir: ')
            print('{}'.format(self.sessionDir))
            print('Series Dirs: ')

            currentTime = int(time.time())
            for s in seriesDirs:
                # get the info from this series dir
                dirName = s[0].split('/')[-1]

                # add to self.seriesDirs

                # calculate & format directory size
                dirSize = sum([os.path.getsize(join(s[0], f)) for f in os.listdir(s[0])])
                if dirSize < 1000:
                    size_string = '{:5.1f} bytes'.format(dirSize)
                elif 1000 <= dirSize < 1000000:
                    size_string = '{:5.1f} kB'.format(dirSize/1000)
                elif 1000000 <= dirSize:
                    size_string = '{:5.1f} MB'.format(dirSize/1000000)

                # calculate time (in mins/secs) since it was modified
                mTime = s[1]
                timeElapsed = currentTime - mTime
                m,s = divmod(timeElapsed,60)
                time_string = '{} min, {} s ago'.format(int(m),int(s))

                print('    {}\t{}\t{}'.format(dirName, size_string, time_string))


    def _findAllSubdirs(self, parentDir):
        """
        Return a list of all subdirectories within the specified
        parentDir, along with the modification time for each

        output: [[subDir_path, subDir_modTime]]
        """
        subDirs = [join(parentDir, d) for d in os.listdir(parentDir) if os.path.isdir(join(parentDir, d))]
        if not subDirs:
            subDirs = None
        else:
            # add the modify time for each directory
            subDirs = [[path, os.stat(path).st_mtime] for path in subDirs]

        # return the subdirectories
        return subDirs

    def waitForSeriesDir(self, interval=.1):
        """
        listen for the creation of a new series directory.
        Once a scan starts, a new series directory will be created
        in the sessionDir. By the time this function is called, this
        class should already have the sessionDir defined
        """
        startTime = int(time.time())    # tag the start time
        keepWaiting = True
        while keepWaiting:
            # obtain a list of all directories in sessionDir
            childDirs = [join(self.sessionDir, d) for d in os.listdir(self.sessionDir) if os.path.isdir(join(self.sessionDir, d))]

            # loop through all dirs, check modification time
            for thisDir in childDirs:
                thisDir_mTime = os.path.getmtime(thisDir)
                if thisDir_mTime > startTime:
                    seriesDir = thisDir
                    keepWaiting = False
                    break

            # pause before searching directories again
            time.sleep(interval)

        # return the found series directory
        return seriesDir



class Siemens_BuildNifti():
    """
    Build a 3D or 4D Nifti image from all of the dicom mosaic images in a
    directory.

    Input is a path to a series directory containing dicom mosaic images. Image
    parameters, like voxel spacing and dimensions, are obtained automatically
    from the info in the dicom tags

    Output is a Nifti1 formatted 3D (anat) or 4D (func) file
    """
    def __init__(self, seriesDir):
        """
        Initialize class:
            - seriesDir needs to be the full path to a directory containing
            raw dicom slices
        """
        # initialize attributes
        self.seriesDir = seriesDir
        self.niftiImage = None
        self.affine = None

        # make a list of all of the raw dicom files in this dir
        rawDicoms = [f for f in os.listdir(self.seriesDir) if Siemens_filePattern.match(f)]

        # figure out what type of image this is, 4d or 3d
        self.scanType = self._determineScanType(rawDicoms[0])

        # build the nifti image
        if self.scanType == 'anat':
            self.niftiImage = self.buildAnat(rawDicoms)
        elif self.scanType == 'func':
            self.niftiImage = self.buildFunc(rawDicoms)

    def buildAnat(self, dicomFiles):
        """
        Given a list of dicomFile paths, build a 3D anatomical image from
        them. Figure out the image dimensions and affine transformation to
        map from voxels to mm from the dicom tags
        """
        print('Add methods for building an anat file!!')


    def buildFunc(self, dicomFiles):
        """
        Given a list of dicomFile paths, build a 4d functional image. For
        Siemens scanners, each dicom file is assumed to represent a mosaic
        image comprised of mulitple slices. This tool will split apart the
        mosaic images, and construct a 4D nifti file. The image dimensions
        and affine transformation to map from voxels to mm will be determined
        from the dicom tags
        """
        ### Figure out the overall 4D image dimensions
        # each mosaic file represents one volume
        nVols = len(dicomFiles)

        # read the dicom tags from one mosaic file to get additional info
        dcm = dicom.read_file(join(self.seriesDir, dicomFiles[0]))
        sliceThickness = getattr(dcm, 'SliceThickness')
        voxSize = getattr(dcm, 'PixelSpacing')

        # private tags in mosaic file
        sliceDims = dcm[0x0051, 0x100b].value.split('*')  # tag: [AcquisitionMatrixText]
        sliceDims = list(map(int, sliceDims))       # convert to integers
        nSlices = dcm[0x0019, 0x100a].value # tag: [NumberOfImagesInMosaic]

        ### figure out how slices are arranged in mosaic
        mosaic_pixels = dcm.pixel_array        # numpy array of all mosaic pixels
        mosaicDims_px = mosaic_pixels.shape    # mosaic dims in pixels

        # figure out the mosaic dimensions in terms of slices
        mosaicDims_slices = np.array([int(mosaicDims_px[0]/sliceDims[0]),
                                        int(mosaicDims_px[1]/sliceDims[1])])

        ### Build a 4D array to store voxel data
        imageMatrix = np.zeros(shape=(
                                sliceDims[0],
                                sliceDims[1],
                                nSlices,
                                nVols),
                                dtype='int16')
        print('Nifti image dims: {}'.format(imageMatrix.shape))

        ### Assemble 4D matrix. Loop over each mosaic, extract slices,
        # add to imageMatrix
        for m in dicomFiles:

            # get volume Idx from the file name (note: needs to be 0-based)
            volIdx = int(Siemens_mosaicVolumeNumberField.search(m).group(0))-1

            # read the mosaic file
            dcm = dicom.read_file(join(self.seriesDir, m))
            mosaic_pixels = dcm.pixel_array

            # grab each slice from this mosaic, add to image matrix
            for slIdx in range(nSlices):

                # figure out where the pixels for this slice start in the mosaic
                sl_rowIdx, sl_colIdx = self._determineSlicePixelIndices(
                                                    mosaicDims_slices,
                                                    sliceDims,
                                                    slIdx)

                # extract this slice from the mosaic
                thisSlice = mosaic_pixels[sl_rowIdx:sl_rowIdx+sliceDims[0],
                                            sl_colIdx:sl_colIdx+sliceDims[1]]

                # Siemens Dicom images appear to follow the DICOM standard
                # of collecting images in an LPS+ coordinate system. Pyneal
                # (and many other neuroimaging tools) expect the coordinate
                # system to be RAS+. To convert, we need to flip our data
                # along the first axis (left/right), and then flip along the
                # 2nd axis (up/down). This is equivalent to rotating the array
                # 180 degrees (less steps = better)
                thisSlice = np.rot90(thisSlice, k=2)

                # Numpy arrays are indexed as [row, col], which in cartesian
                # coords translates to [y,x]. We want our data to be an array
                # that is indexed like [x,y,z,t], so we need to transpose
                # each slice before adding to the full image matrix
                imageMatrix[:,:,slIdx, volIdx] = thisSlice.T

        ### Create the affine transformation that will map from vox to mm
        # space. Our reference space (in mm) will have the same origin and
        # axes as the voxel array. So, our affine transform just needs to be
        # a scale transform that scales each dimension to the appropriate
        # voxel size
        affine = np.diag([voxSize[0], voxSize[1], sliceThickness, 1])

        ### Build a Nifti object
        funcImage = nib.Nifti1Image(imageMatrix, affine=affine)

        return funcImage


    def _determineSlicePixelIndices(self, mosaicDims, sliceDims, sliceIdx):
        """
        Figure out the mosaic pixel indices that correspond to a given slice
        index (0-based)

        mosaicDims: dimensions of the mosaic in terms of number of slices
        sliceDims: dimensions of the slice in terms of pixels
        sliceIdx: the index value of the slice you want to find

        Returns: rowIdx, colIdx
            - row and column index of starting pixel for this slice
        """
        # determine where this slice is in the mosaic
        mWidth = mosaicDims[1]
        mRow= int(np.floor(sliceIdx/mWidth))
        mCol = int(sliceIdx % mWidth)

        rowIdx = mRow*sliceDims[0]
        colIdx = mCol*sliceDims[1]

        return rowIdx, colIdx


    def _determineScanType(self, dicomFile):
        """
        Figure out what type of scan this is, single 3D volume (anat), or
        a 4D dataset built up of 2D slices (func) based on info found
        in the dicom tags
        """
        # read the dicom file
        dcm = dicom.read_file(join(self.seriesDir, dicomFile), stop_before_pixels=1)

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


    def write_nifti(self, output_fName):
        """
        write the nifti file to disk using the abs path
        specified by output_fName
        """
        nib.save(self.niftiImage, output_fName)


class Siemens_monitorSeriesDir(Thread):
    """
    Class to monitor for new mosaic images to appear in the seriesDir. This
    class will run independently in a separate thread. Each new mosaic file
    that appears will be added to the Queue for further processing
    """
    def __init__(self, seriesDir, dicomQ, interval=.5):
        # start the thread upon completion
        Thread.__init__(self)

        # set up logger
        self.logger = logging.getLogger(__name__)

        # initialize class parameters
        self.interval = interval            # interval for polling for new files
        self.seriesDir = seriesDir          # full path to series directory
        self.dicomQ = dicomQ                # queue to store dicom mosaic files
        self.alive = True                   # thread status
        self.numMosaicsAdded = 0            # counter to keep track of # mosaics
        self.queued_mosaic_files = set()    # empty set to store names of queued mosaic

    def run(self):
        # function that runs while the Thread is still alive
        while self.alive:

            # create a set of all mosaic files currently in the series dir
            currentMosaics = set(os.listdir(self.seriesDir))

            # grab only the ones that haven't already been added to the queue
            newMosaics = [f for f in currentMosaics if f not in self.queued_mosaic_files]

            # loop over each of the new mosaic files, add each to queue
            for f in newMosaics:
                mosaic_fname = join(self.seriesDir, f)
                try:
                    self.dicomQ.put(mosaic_fname)
                except:
                    self.logger.error('failed on: {}'.format(mosaic_fname))
                    print(sys.exc_info())
                    sys.exit()
            if len(newMosaics) > 0:
                self.logger.debug('Put {} new slices on the queue'.format(len(newMosaics)))
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
    dividing it up into individual slices, reformatting each slice, and then
    sending each slice out over the socket connection
    """
    def __init__(self, dicomQ, scannerSocket, interval=.2):
        # start the threat upon creation
        Thread.__init__(self)

        # set up logger
        self.logger = logging.getLogger(__name__)

        # initialize class parameters
        self.dicomQ = dicomQ
        self.interval = interval        # interval between polling queue for new files
        self.alive = True
        self.scannerSocket = scannerSocket
        self.totalProcessed = 0         # counter for total number of slices processed
        self.nSlicesPerVol = None       # once set, won't need to be retrieved each time
        self.mosaicDims_slices = None   # mosaic dims in slices, only needs to be set once
        self.sliceDims = None           # slice dimensions in pixels, only needs to be set once

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
        Read the dicom mosaic file. Extract each slice out of it,
        build a header for each slice, and end out over the scanner
        socket connection

        mosaic_dcm_fname: full path to the mosaic file
        """

        ### Figure out the volume index for this mosaic by reading
        # the field from the file name itself
        mosaicFile_root, mosaicFile_name = os.path.split(mosaic_dcm_fname)
        volIdx = int(Siemens_mosaicVolumeNumberField.search(mosaicFile_name).group(0))-1

        # read the dicom file
        dcm = dicom.read_file(mosaic_dcm_fname)
        mosaic_pixels = dcm.pixel_array

        # figure out the fixed values for this scan
        if self.nSlicesPerVol is None:
            self.nSlicesPerVol = dcm[0x0019, 0x100a].value  # private tag: [NumberOfImagesInMosaic]
        if self.sliceDims is None:
            sliceDims = dcm[0x0051, 0x100b].value.split('*')   # tag: [AcquisitionMatrixText]
            self.sliceDims = list(map(int, sliceDims))              # convert to integers
        if self.mosaicDims_slices is None:
            mosaicDims_px = mosaic_pixels.shape    # mosaic dims in pixels
            self.mosaicDims_slices = np.array([int(mosaicDims_px[0]/self.sliceDims[0]),
                                             int(mosaicDims_px[1]/self.sliceDims[1])])

        ### Loop over each slice in the mosaic:
        for slIdx in range(self.nSlicesPerVol):
            #figure out where the pixels for this slice start in the mosaic
            sl_rowIdx, sl_colIdx = self._determineSlicePixelIndices(slIdx)
            
            # extract this slice from the mosaic
            thisSlice = mosaic_pixels[sl_rowIdx:sl_rowIdx + self.sliceDims[0],
                                        sl_colIdx:sl_colIdx + self.sliceDims[1]]

            # Siemens Dicom images appear to follow the DICOM standard
            # of collecting images in an LPS+ coordinate system. Pyneal
            # (and many other neuroimaging tools) expect the coordinate
            # system to be RAS+. To convert, we need to flip our data
            # along the first axis (left/right), and then flip along the
            # 2nd axis (up/down). This is equivalent to rotating the array
            # 180 degrees (less steps = better)
            thisSlice = np.ascontiguousarray(
                        np.rot90(thisSlice, k=2)
                        )

            # Numpy arrays are indexed as [row, col], which in cartesian
            # coords translates to [y,x]. We want our data to be an array
            # that is indexed like [x,y,z,t], so we need to transpose
            # each slice before adding to the full image matrix
            thisSlice = thisSlice.T

            ### Format the header
            sliceHeader = {
                'sliceIdx': slIdx,
                'volIdx': volIdx,
                'nSlicesPerVos': self.nSlicesPerVol,
                'dtype':str(thisSlice.dtype),
                'shape':thisSlice.shape
                }

            ### Send the slice array ad the header to the scanner socket
            self.sendSliceToScannerSocket(sliceHeader, thisSlice)


    def _determineSlicePixelIndices(self, sliceIdx):
        """
        Figure out the mosaic pixel indices that correspond to a given slice
        index (0-based)

        sliceIdx: the index value of the slice you want to find

        Returns: rowIdx, colIdx
            - row and column index of starting pixel for this slice
        """
        # determine where this slice is in the mosaic
        mWidth = self.mosaicDims_slices[1]
        mRow= int(np.floor(sliceIdx/mWidth))
        mCol = int(sliceIdx % mWidth)

        rowIdx = mRow * self.sliceDims[0]
        colIdx = mCol * self.sliceDims[1]

        return rowIdx, colIdx


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


def Siemens_launch_rtfMRI(scannerSettings, scannerDirs):
    """
    launch a real-time session in a Siemens environment. This should be called
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
    from .general_utils import create_scannerSocket
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
    scanWatcher = Siemens_monitorSeriesDir(seriesDir, dicomQ)
    scanWatcher.start()

    # create an instance of the class that will grab slice dicoms
    # from the queue, reformat the data, and pass over the socket
    # to pyneal. Start the thread going
    mosaicProcessor = Siemens_processMosaic(dicomQ, scannerSocket)
    mosaicProcessor.start()




if __name__ == '__main__':
    testSeriesDir = '../../../sandbox/scansForSimulation/Siemens_UNC/series0999'

    dicomQ = Queue()
    scanWatcher = Siemens_monitorSeriesDir(testSeriesDir, dicomQ)


    outputFile = '../data/siemensOutput.nii.gz'
    #outputFile = '/Users/jeff/Desktop/test.nii.gz'
    testSiemens.write_nifti(outputFile)
