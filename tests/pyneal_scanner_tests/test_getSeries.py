""" Test functions in pyneal/pyneal_scanner/getSeries.py module """

import os
from os.path import join
import sys

from helper_tools import *

# get dictionary with relevant paths for tests within this module
paths = get_pyneal_scanner_test_paths()
sys.path.insert(0, paths['pynealDir'])
sys.path.insert(0, paths['pynealScannerDir'])

import pyneal_scanner.utils.general_utils as general_utils


def test_getSeries_GE():
    """ test getSeries.getSeries_GE """

    GE_dir = paths['GE_dir']
    GE_funcDir = paths['GE_funcDir']

    # update config file to match local paths
    configFile = join(GE_dir, 'scannerConfig.yaml')
    replace_scannerConfig_baseDir(configFile, GE_funcDir)

    # run initializeSettings to get the scannerDirs object
    scannerSettings, scannerDirs = general_utils.initializeSession(pynealScannerDir=GE_dir)

    ### run getSeries_GE
    import pyneal_scanner.getSeries as getSeries

    # module expects user to input 2 things: desired series, and output prefix.
    # We have to mock the input for automatic testing, but can only mock one
    # input (at least as far as I can figure out). So, by hardcoding the input
    # to 's1925', we will get series s1925 and build a nifti named
    # 's1925_s1925.nii.gz' saved in pyneal/pyneal_scanner/data. Delete this file
    # at end of test
    getSeries.input = lambda x: 's1925'
    getSeries.getSeries_GE(scannerDirs)

    # return the module input to the normal __builtin__ input function
    getSeries.input = input

    # ensure output file created, then delete
    outputFile = join(paths['pynealScannerDir'], 'data/s1925_s1925.nii.gz')
    assert os.path.exists(outputFile)
    os.remove(outputFile)
