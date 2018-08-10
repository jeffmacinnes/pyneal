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

    envDir = paths['GE_dir']
    funcDir = paths['GE_funcDir']

    # update config file to match local paths
    configFile = join(envDir, 'scannerConfig.yaml')
    replace_scannerConfig_baseDir(configFile, funcDir)

    # run initializeSettings to get the scannerDirs object
    scannerSettings, scannerDirs = general_utils.initializeSession(pynealScannerDir=envDir)

    ### run getSeries_GE
    import pyneal_scanner.getSeries as getSeries

    # module expects user to input 2 things: desired series, and output prefix.
    # We have to mock the input for automatic testing, but can only mock one
    # input (at least as far as I can figure out). So, by hardcoding the input
    # to 's1925', we will get series s1925 and build a nifti named
    # 's1925_s1925.nii.gz' saved in pyneal/pyneal_scanner/data. Delete this file
    # at end of test
    seriesNum = 's1925'
    getSeries.input = lambda x: seriesNum
    getSeries.getSeries_GE(scannerDirs)

    # return the module input to the normal __builtin__ input function
    getSeries.input = input

    # ensure output file created, then delete
    outputFile = join(paths['pynealScannerDir'], 'data', '{}_{}.nii.gz'.format(seriesNum, seriesNum))
    assert os.path.exists(outputFile)
    os.remove(outputFile)


def test_getSeries_Philips():
    """ test getSeries.getSeries_Philips """

    envDir = paths['Philips_dir']
    funcDir = paths['Philips_funcDir']

    # update config file to match local paths
    configFile = join(envDir, 'scannerConfig.yaml')
    replace_scannerConfig_baseDir(configFile, funcDir)

    # run initializeSettings to get the scannerDirs object
    scannerSettings, scannerDirs = general_utils.initializeSession(pynealScannerDir=envDir)

    ### run getSeries_Philips
    import pyneal_scanner.getSeries as getSeries

    # module expects user to input 2 things: desired series, and output prefix.
    # We have to mock the input for automatic testing, but can only mock one
    # input (at least as far as I can figure out). So, by hardcoding the input
    # to '0001', we will get series 0001 and build a nifti named
    # '0001_0001.nii.gz' saved in pyneal/pyneal_scanner/data. Delete this file
    # at end of test
    seriesNum = '0001'
    getSeries.input = lambda x: seriesNum
    getSeries.getSeries_Philips(scannerDirs)

    # return the module input to the normal __builtin__ input function
    getSeries.input = input

    # ensure output file created, then delete
    outputFile = join(paths['pynealScannerDir'], 'data', '{}_{}.nii.gz'.format(seriesNum, seriesNum))
    assert os.path.exists(outputFile)
    os.remove(outputFile)


def test_getSeries_Siemens():
    """ test getSeries.getSeries_Siemens """

    envDir = paths['Siemens_dir']
    funcDir = paths['Siemens_funcDir']

    # update config file to match local paths
    configFile = join(envDir, 'scannerConfig.yaml')
    replace_scannerConfig_baseDir(configFile, funcDir)

    # run initializeSettings to get the scannerDirs object
    scannerSettings, scannerDirs = general_utils.initializeSession(pynealScannerDir=envDir)

    ### run getSeries_Siemens
    import pyneal_scanner.getSeries as getSeries

    # module expects user to input 2 things: desired series, and output prefix.
    # We have to mock the input for automatic testing, but can only mock one
    # input (at least as far as I can figure out). So, by hardcoding the input
    # to '000013', we will get series 000013 and build a nifti named
    # '000013_000013.nii.gz' saved in pyneal/pyneal_scanner/data. Delete this file
    # at end of test
    seriesNum = '000013'
    getSeries.input = lambda x: seriesNum
    getSeries.getSeries_Siemens(scannerDirs)

    # return the module input to the normal __builtin__ input function
    getSeries.input = input

    # ensure output file created, then delete
    outputFile = join(paths['pynealScannerDir'], 'data', '{}_{}.nii.gz'.format(seriesNum, seriesNum))
    assert os.path.exists(outputFile)
    os.remove(outputFile)
