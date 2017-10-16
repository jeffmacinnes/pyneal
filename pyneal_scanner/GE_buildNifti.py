"""
Build a 3D or 4D Nifti image from all of the dicom slice imagas in a directory.

User supplies path to a series directory containing dicom slices. Image
parameters, like voxel spacing and dimensions, are obtained automatically
from info in the dicom tags

"""
from __future__ import print_function
from __future__ import division

import os
from os.path import join
import sys
import re

import numpy as np
import dicom
import nibabel as nib
import argparse

# regEx for GE style file naming
GE_filePattern = re.compile('i\d*.MRDC.\d*')

class NiftiBuilder():
    """
    methods and attributes needed to build a nifti image from raw dicom slices
    """

    def __init__(self, seriesDir):
        # initialize attributes
        self.seriesDir = seriesDir
        self.affine = None

        # make a list of all of the dicoms in this dir
        rawDicoms = [f for f in os.listdir(seriesDir) if GE_filePattern.match(f)]

        # figure out what type of image this is, 4d or 3d
        self.scanType = self.getScanType(rawDicoms[0])

        if self.scanType == 'anat':
            self.dataset, self.affine = self.buildAnat(rawDicoms)
        elif self.scanType == 'func':
            self.dataset, self.affine = self.buildFunc(rawDicoms)

        #### TMP
        fName = os.path.split(self.seriesDir)[-1]
        print('fNAME: {}'.format(fName))
        testImage = nib.Nifti2Image(self.dataset, affine=self.affine)
        hdr = testImage.header
        hdr.set_sform(np.diag([2,2,2,1]), code='mni')
        print(testImage.header)

        #testImage.update_header()

        nib.save(testImage, (fName+'.nii.gz'))
        #testImage.to_filename(fName + '.nii.gz')


    def buildAnat(self, dicomFiles):
        """
        Given a list of dicomFiles, build a 3D anatomical image from them.
        Figure out the image dimensions and affine transformation to map
        from voxels to mm from the dicom tags
        """

        # read the first dicom in the list to get overall image dimensions
        dcm = dicom.read_file(join(self.seriesDir, dicomFiles[0]), stop_before_pixels=1)
        sliceDims = (getattr(dcm, 'Rows'), getattr(dcm, 'Columns'))
        nSlices = getattr(dcm, 'ImagesInAcquisition')

        # create an empty array to store the slice data
        imageMatrix = np.zeros(shape=(
                                sliceDims[0],
                                sliceDims[1],
                                nSlices)
                            )
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
            if sliceIdx == nSlices-1:
                lastSliceDcm = dcm

            # put this pixel data in the image matrix
            pixel_array = dcm.pixel_array
            pixel_array = np.fliplr(pixel_array)
            pixel_array = np.flipud(pixel_array)
            imageMatrix[:, :, sliceIdx] = pixel_array.T

        # create the affine transformation to map from vox to mm space
        affine = self.createAffine(firstSliceDcm, lastSliceDcm)
        affine = np.eye(4)
        #affine = np.diag([2,2,2,1])

        return imageMatrix, affine


    def createAffine(self, firstSlice, lastSlice):
        """
        build an affine transformation matrix that maps from voxel
        space to mm space.

        For helpful info on how to build this, see:
        http://nipy.org/nibabel/dicom/dicom_orientation.html &
        http://nipy.org/nibabel/coordinate_systems.html
        """

        # initialize an empty 4x4 matrix that will serve as our
        # affine transformation. This will allow us to combine
        # rotations and translations into the same transform
        affine = np.zeros(shape=(4,4))

        # but we need to make sure the bottom right position is set to 1
        affine[3,3] = 1

        # affine[:3, :2] reprsents the rotations needed to position our voxel
        # array in reference space. We can safely assume these rotations will
        # be the same for all slices in our 3D volume, so we can just grab the
        # ImageOrientationPatient tag from the first slice only...
        imageOrientation = getattr(firstSlice, 'ImageOrientationPatient')

        # multiply the imageOrientation values by the voxel size
        voxSize = getattr(firstSlice, 'PixelSpacing')
        imageOrientation = np.array(imageOrientation)*voxSize[0]

        # ...and populate the affine matrix
        affine[:3,0] = imageOrientation[:3]
        affine[:3,1] = imageOrientation[3:]

        # affine[:3,3] represents the translations along the x,y,z axis,
        # respectively, that would bring voxel location 0,0,0 to the origin
        # of the reference space. Thus, we can grab these 3 values from the
        # ImagePositionPatient tag of the first slice as well
        # (first slice is z=0, so has voxel 0,0,0):
        imagePosition = getattr(firstSlice, 'ImagePositionPatient')

        # ...and populate the affine matrix
        affine[:3,3] = imagePosition

        # affine[:3,2] represents the translations needed to go from the first
        # slice to the last slice. So we need to know the positon of the last slice
        # before we can fill in these values. First, we figure out the spatial difference
        # between the first and last slice.
        firstSliceImagePos = getattr(firstSlice, 'ImagePositionPatient')
        lastSliceImagePos = getattr(lastSlice, 'ImagePositionPatient')
        positionDiff = np.array([
                            firstSliceImagePos[0] - lastSliceImagePos[0],
                            firstSliceImagePos[1] - lastSliceImagePos[1],
                            firstSliceImagePos[2] - lastSliceImagePos[2]
                        ])

        # divide each element of the difference in position by 1-numSlices
        numSlices = getattr(firstSlice, 'ImagesInAcquisition')
        positionDiff = positionDiff/(1-numSlices)

        # ...and populate the affine
        affine[:3,2] = positionDiff

        # all done, return the affine
        return affine


    def getScanType(self, sliceDcm):
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







if __name__ == '__main__':

    # set up arg parser:
    parser = argparse.ArgumentParser()
    parser.add_argument('seriesDir',
                        help="Path to the series directory (i.e. where dicom slices images are stored)")
    # retrieve the args
    args = parser.parse_args()

    # build nifti for this dir
    a = NiftiBuilder(args.seriesDir)
