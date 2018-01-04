"""
Set of classes and methods specific to GE scanning environments
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

# regEx for GE style file naming
GE_filePattern = re.compile('i\d*.MRDC.\d*')

class GE_DirStructure():
    """
    Methods for finding and returning the names and paths of
    series directories in a GE scanning environment

    In GE enviroments, a new folder is created for every series (i.e. each
    unique scan). The series folders are typically named like 's###'. While
    the number for the first series cannot be predicted, subsequent series
    directories tend to (but not necessarily, it turns out) be numbered
    sequentially

    All of the series directories for a given session (or 'exam' in GE-speak)
    are stored in an exam folder, named like 'e###', where the number is
    unpredictable. Likewise, each exam folder is stored in a parent folder,
    named like 'p###' where the number is unpredictable. The p### directories
    are stored in a baseDir which (thankfully) tends to be a fixed path.

    So, in other words, new series show up in a unique directory with an
    absolute path like:
    [baseDir]/p###/e###/s###

    Throughout, we'll sometimes refer to the directory that contains
    the s### directories as the 'sessionDir'. So,

    sessionDir = [baseDir]/p###/e###

    This class contains methods to retrieve THE MOST RECENTLY modified
    sessionDir directories, as well as a list of all s### directories along
    with timestamps and directory sizes. This will hopefully allow users to
    match a particular task scan (e.g. anatomicals, or experimentRun1) with
    the full path to its raw data on the scanner console
    """
    def __init__(self, scannerSettings):
        # initialize the class attributes
        if 'scannerBaseDir' in scannerSettings.allSettings:
            self.baseDir = scannerSettings.allSettings['scannerBaseDir']
        else:
            print('No scannerBaseDir found in scannerConfig file. Using default: {}'.format(GE_default_baseDir))
            self.baseDir = GE_default_baseDir

        self.pDir = None
        self.eDir = None
        self.sessionDir = None
        self.seriesDirs = None

        # (hopefully) find and initialize the sessionDir (and subdirs)
        self.findSessionDir()


    def findSessionDir(self):
        """
        Find the most recently modified p###/e### directory in the
        baseDir
        """
        try:
            # Find the most recent p### dir
            try:
                # Find all subdirectores in the baseDir
                pDirs = self._findAllSubdirs(self.baseDir)

                # remove any dirs that don't start with p
                pDirs = [x for x in pDirs if os.path.split(x[0])[-1][0] == 'p']

                # sort based on modification time, take the most recent
                pDirs = sorted(pDirs, key=lambda x: x[1], reverse=True)
                newest_pDir = pDirs[0][0]

                # just the p### portion
                pDir = os.path.split(newest_pDir)[-1]

            except:
                print('Error: Could not find any p### dirs in {}'.format(self.baseDir))

            # Find the most recent e### dir
            try:
                # find all subdirectories in the most recent p### dir
                eDirs = self._findAllSubdirs(newest_pDir)

                # remove any dirs that don't start with e
                eDirs = [x for x in eDirs if os.path.split(x[0])[-1][0] == 'e']

                # sort based on modification time, take the most recent
                eDirs = sorted(eDirs, key=lambda x: x[1], reverse=True)
                newest_eDir = eDirs[0][0]

                # just the e### portion
                eDir = os.path.split(newest_eDir)[-1]

            except:
                print('Error: Could not find an e### dirs in {}'.format(newest_pDir))

            # set the session dir as the full path including the eDir
            sessionDir = newest_eDir
        except:
            print('Error: Failed to find a sessionDir')
            sessionDir = None
            pDir = None
            eDir = None

        # set values to these attributes
        self.pDir = pDir
        self.eDir = eDir
        self.sessionDir = sessionDir


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


    def get_seriesDirs(self):
        """
        build a list that contains the directory names of all of the series
        """
        # get a list of all sub dirs in the sessionDir
        subDirs = self._findAllSubdirs(self.sessionDir)

        if subDirs is not None:
            # extract just the dirname from subDirs and append to a list
            self.seriesDirs = []
            for d in subDirs:
                self.seriesDirs.append(d[0].split('/')[-1])
        else:
            self.seriesDirs = None

        return self.seriesDirs


    def get_pDir(self):
        return self.pDir


    def get_eDir(self):
        return self.eDir


    def get_sessionDir(self):
        return self.sessionDir


class GE_BuildNifti():
    """
    Build a 3D or 4D Nifti image from all of the dicom slice images in a directory.

    Input is a path to a series directory containing dicom slices. Image
    parameters, like voxel spacing and dimensions, are obtained automatically
    from info in the dicom tags

    Output is a Nifti1 formatted 3D (anat) or 4D (func) file
    """
    def __init__(self, seriesDir):
        """
        Initialize class:
            - seriesDir needs to be the full path to directory containing
            raw dicom slices
        """
        # initialize attributes
        self.seriesDir = seriesDir
        self.niftiImage = None

        self.affine = None
        self.pixelSpacing = None        # pixel spacing attribute from dicom tag
        self.firstSlice_IOP = None      # first slice ImageOrientationPatient tag
        self.firstSlice_IPP = None      # first slice ImagePositionPatient tag
        self.lastSlice_IPP = None       # last slice ImagePositionPatient tag
        self.nSlicesPerVol = None       # number of slices per volume

        # make a list of all of the dicoms in this dir
        self.rawDicoms = [f for f in os.listdir(self.seriesDir) if GE_filePattern.match(f)]

        # figure out what type of image this is, 4d or 3d
        self.scanType = self._determineScanType(self.rawDicoms[0])
        if self.scanType == 'anat':
            self.niftiImage = self.buildAnat(self.rawDicoms)
        elif self.scanType == 'func':
            self.niftiImage = self.buildFunc(self.rawDicoms)


    def buildAnat(self, dicomFiles):
        """
        Given a list of dicomFiles, build a 3D anatomical image from them.
        Figure out the image dimensions and affine transformation to map
        from voxels to mm from the dicom tags
        """
        # read the first dicom in the list to get overall image dimensions
        dcm = dicom.read_file(join(self.seriesDir, dicomFiles[0]), stop_before_pixels=1)
        sliceDims = (getattr(dcm, 'Columns'), getattr(dcm, 'Rows'))
        self.nSlicesPerVol = getattr(dcm, 'ImagesInAcquisition')
        sliceThickness = getattr(dcm, 'SliceThickness')
        voxSize = getattr(dcm, 'PixelSpacing')

        ### Build 3D array of voxel data
        # create an empty array to store the slice data
        imageMatrix = np.zeros(shape=(
                                sliceDims[0],
                                sliceDims[1],
                                self.nSlicesPerVol),
                                dtype='int16')

        print('Nifti image dims: {}'.format(imageMatrix.shape))

        # With functional data, the dicom tag 'InStackPositionNumber'
        # seems to correspond to the slice index (one-based indexing).
        # But with anatomical data, there are 'InStackPositionNumbers'
        # that may start at 2, and go past the total number of slices.
        # To correct, we first pull out all of the InStackPositionNumbers,
        # and create a dictionary with InStackPositionNumbers:dicomPath
        # keys. Sort by the position numbers, and assemble the image in order
        sliceDict = {}
        for s in dicomFiles:
            dcm = dicom.read_file(join(self.seriesDir, s))
            sliceDict[dcm.InStackPositionNumber] = join(self.seriesDir, s)

        # sort by InStackPositionNumber and assemble the image
        for sliceIdx,ISPN in enumerate(sorted(sliceDict.keys())):
            dcm = dicom.read_file(sliceDict[ISPN])

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

        dcm_first = dicom.read_file(firstSlice)
        dcm_last = dicom.read_file(lastSlice)
        self.pixelSpacing = getattr(dcm_first, 'PixelSpacing')
        self.firstSlice_IOP = np.array(getattr(dcm_first, 'ImageOrientationPatient'))
        self.firstSlice_IPP = np.array(getattr(dcm_first, 'ImagePositionPatient'))
        self.lastSlice_IPP = np.array(getattr(dcm_last, 'ImagePositionPatient'))

        # now we can build the affine
        affine = self.buildAffine()

        ### Build a Nifti object, reorder it to RAS+
        anatImage = nib.Nifti1Image(imageMatrix, affine=affine)
        anatImage_RAS = nib.as_closest_canonical(anatImage)     # reoder to RAS+

        return anatImage_RAS


    def buildFunc(self, dicomFiles):
        """
        Given a list of dicomFiles, build a 4D functional image from them.
        Figure out the image dimensions and affine transformation to map
        from voxels to mm from the dicom tags
        """
        # read the first dicom in the list to get overall image dimensions
        dcm = dicom.read_file(join(self.seriesDir, dicomFiles[0]), stop_before_pixels=1)
        sliceDims = (getattr(dcm, 'Columns'), getattr(dcm, 'Rows'))
        self.nSlicesPerVol = getattr(dcm, 'ImagesInAcquisition')
        nVols = getattr(dcm, 'NumberOfTemporalPositions')
        sliceThickness = getattr(dcm, 'SliceThickness')
        voxSize = getattr(dcm, 'PixelSpacing')

        ### Build 4D array of voxel data
        # create an empty array to store the slice data
        imageMatrix = np.zeros(shape=(
                                sliceDims[0],
                                sliceDims[1],
                                self.nSlicesPerVol,
                                nVols),
                                dtype='int16'
                            )
        print('Nifti image dims: {}'.format(imageMatrix.shape))

        ### Assemble 4D matrix
        # loop over every dicom file
        for s in dicomFiles:

            # read in the dcm file
            dcm = dicom.read_file(join(self.seriesDir, s))

            # The dicom tag 'InStackPositionNumber' will tell
            # what slice number within a volume this dicom is.
            # Note: InStackPositionNumber uses one-based indexing
            sliceIdx = getattr(dcm, 'InStackPositionNumber') - 1

            # Get the tags needed for the affine transform, if this is
            # either the first or last slice
            if sliceIdx == 0 and self.firstSlice_IOP is None:
                self.pixelSpacing = getattr(dcm, 'PixelSpacing')
                self.firstSlice_IOP = np.array(getattr(dcm, 'ImageOrientationPatient'))
                self.firstSlice_IPP = np.array(getattr(dcm, 'ImagePositionPatient'))

            if sliceIdx == (self.nSlicesPerVol-1) and self.lastSlice_IPP is None:
                self.lastSlice_IPP = np.array(getattr(dcm, 'ImagePositionPatient'))

            # We can figure out the volume index using the dicom
            # tags "InstanceNumber" (# out of all images), and
            # "ImagesInAcquisition" (# of slices in a single vol).
            # Divide InstanceNumber by ImagesInAcquisition and drop
            # the remainder. Note: InstanceNumber is also one-based index
            instanceIdx = getattr(dcm, 'InstanceNumber')-1
            volIdx = int(np.floor(instanceIdx/self.nSlicesPerVol))

            # We need our data to be an array that is indexed like [x,y,z,t],
            # so we need to transpose each slice from [row,col] to [col,row]
            # before adding to the full dataset
            imageMatrix[:, :, sliceIdx, volIdx] = dcm.pixel_array.T

        ### create the affine transformation to map from vox to mm space
        affine = self.buildAffine()

        ### Build a Nifti object, reorder it to RAS+
        funcImage = nib.Nifti1Image(imageMatrix, affine=affine)
        funcImage_RAS = nib.as_closest_canonical(funcImage)     # reoder to RAS+

        return funcImage_RAS


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



    def _determineScanType(self, sliceDcm):
        """
        Figure out what type of scan this is, single 3D volume (anat), or
        a 4D dataset built up of 2D slices (func) based on info found
        in the dicom tags
        """
        # read the dicom file
        dcm = dicom.read_file(join(self.seriesDir, sliceDcm), stop_before_pixels=1)

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


class GE_processSlice(Thread):
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
        dcm = dicom.read_file(dcm_fname)

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
        dcmHdr = dicom.read_file(dcm_fname, stop_before_pixels=True)

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


def GE_launch_rtfMRI(scannerSettings, scannerDirs):
    """
    launch a real-time session in a GE environment. This should be called
    from pynealScanner.py before starting the scanner. Once called, this
    method will take care of:
        - monitoring the sessionDir for a new series directory to appear (and
        then returing the name of the new series dir)
        - set up the socket connection to send volume data over
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
    # volumes as they appear
    # initialize the dicom queue to keep store newly arrived
    # dicom slices, and keep track of which have been processed
    dicomQ = Queue()

    # create instance of class that will monitor seriesDir. Pass in
    # a copy of the dicom queue. Start the thread going
    scanWatcher = GE_monitorSeriesDir(seriesDir, dicomQ)
    scanWatcher.start()

    # create an instance of the class that will grab slice dicoms
    # from the queue, reformat the data, and pass over the socket
    # to pyneal. Start the thread going
    sliceProcessor = GE_processSlice(dicomQ, scannerSocket)
    sliceProcessor.start()
