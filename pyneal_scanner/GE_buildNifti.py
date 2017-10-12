"""
Build a 3D or 4D Nifti image from all of the dicom slice imagas in a directory.

User supplies path to a series directory containing dicom slices. Image
parameters, like voxel spacing and dimensions, are obtained automatically
from info in the dicom tags

"""
from __future__ import print_function

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
        testImage = nib.Nifti1Image(self.dataset, affine=self.affine)
        testImage.to_filename(fName + '.nii.gz')


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

            # put this pixel data in the image matrix
            imageMatrix[:, :, sliceIdx] = dcm.pixel_array


        affine = np.eye(4)

        return imageMatrix, affine



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
