"""
Construct a Nifti-formatted file from the specified series, and transfer it
to the real-time analyis machine.

If the series is an anatomical scan, the output Nifti will be 3D.
If the series is a functional scan, the output Nifti will be 4D.

In all cases, the output image will have RAS+ orientation, and the affine
transformation in the Nifti header will simple convert from voxel space
to mm space using the image voxel sizes (and not moving the origin at all)
"""
from __future__ import print_function

import os
import sys
from os.path import join

from utils.general_utils import ScannerSettings
import listSeries


if __name__ == '__main__':
    listSeries.listSeries()

    # retrieve the sessionDir from the scannerSettings
