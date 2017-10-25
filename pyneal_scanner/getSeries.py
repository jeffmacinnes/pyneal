"""
(Pyneal-Scanner: Command line function)
Calling this function will first prompt the user to specify a
series directory, and an output name for the file. Next, it will construct
a Nifti-formatted file from the specified series, and transfer it to
the real-time analyis machine.

If the series is an anatomical scan, the output Nifti will be 3D.
If the series is a functional scan, the output Nifti will be 4D.

In all cases, the output image will have RAS+ orientation, and the affine
transformation in the Nifti header will simple convert from voxel space
to mm space using the image voxel sizes (and not moving the origin at all)
"""
# python 2/3 compatibility
from __future__ import print_function
if hasattr(__builtins__, 'raw_input'):
    input = raw_input

import os
import sys
from os.path import join

from utils.general_utils import initializeSession


if __name__ == '__main__':

    # initialize the session classes:
    scannerSettings, scannerDirs = initializeSession()

    # print all of the current series dirs to the terminal
    scannerDirs.print_seriesDirs()

    # load the appropriate tools for this scanning environment
    scannerMake = scannerSettings.allSettings['scannerMake']
    if scannerMake == 'GE':
        #from utils.GE_utils import GE_BuildNifti

        # prompt user to specifiy a series. Make sure that it is a valid
        # series before continuing...
        seriesDirs = scannerDirs.get_seriesDirs()
        while True:
            selectedSeries = input('Which Series?:')
            if selectedSeries in seriesDirs:
                print('You selected series: {}'.format(selectedSeries))
                break
            else:
                print('{} is not a valid series choice!'.format(selectedSeries))

        # get the full path to the series dir
        seriesDir = join(scannerDirs.sessionDir, selectedSeries)
        print('full path to series dir: {}'.format(seriesDir))
