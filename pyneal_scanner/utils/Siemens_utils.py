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




if __name__ == '__main__':
    testDir = '../../../sandbox/scansForSimulation/Siemens_UNC/series0013'

    testSiemens = Siemens_BuildNifti(testDir)

    outputFile = '../data/siemensOutput.nii.gz'
    #outputFile = '/Users/jeff/Desktop/test.nii.gz'
    testSiemens.write_nifti(outputFile)
