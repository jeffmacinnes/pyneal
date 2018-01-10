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

# Get the full path to where the pyneal_scanner directory is. This assumes
# getSeries.py was called directly from the command line (currently
# the only option)
pynealScannerDir = os.path.dirname(os.path.abspath(sys.argv[0]))

def getSeries_GE(scannerSettings, scannerDirs):
    """
    Steps for getting offline data from the scanner that are
    specific to GE environments
    """
    from utils.GE_utils import GE_BuildNifti

    # prompt user to specifiy a series. Make sure that it is a valid
    # series before continuing
    seriesDirs = scannerDirs.get_seriesDirs()
    while True:
        selectedSeries = input('Which Series?: ')
        if selectedSeries in seriesDirs:
            break
        else:
            print('{} is not a valid series choice!'.format(selectedSeries))

    # prompt user to specify an output name, and format to remove any spaces
    outputPrefix = input('Output Prefix: ')
    outputPrefix = outputPrefix.replace(' ', '')

    # progress updates
    print('='*5)
    print('Building Nifti...')
    print('\tinput series: {}'.format(selectedSeries))
    print('\toutput prefix: {}'.format(outputPrefix))

    # get the full path to the series dir
    seriesDir = join(scannerDirs.sessionDir, selectedSeries)

    # create an instance of the GE_NiftiBuilder
    niftiBuilder = GE_BuildNifti(seriesDir)
    print('Successfully built Nifti image...\n')

    # ask user whether they want to save it locally or send
    print('Save nifti locally (1), or Send to remote machine (2)')
    while True:
        saveOrSend = input('type 1 or 2: ')
        if saveOrSend in ['1', '2']:
            break
        else:
            print('{} is not a valid choice!'.format(saveOrSend))

    if saveOrSend == '1':
        output_path = join(pynealScannerDir, 'data', '{}_{}.nii.gz'.format(outputPrefix, selectedSeries))
        niftiBuilder.write_nifti(output_path)

    elif saveOrSend == '2':
        pass
        #sendNifti()


def getSeries_Philips(scannerSettings, scannerDirs):
    """
    Steps for getting offline data from the scanner that are
    specific to Phillips environments
    """
    from utils.Philips_utils import Philips_BuildNifti

    # prompt user to specifiy a series. Make sure that it is a valid
    # series before continuing
    seriesDirs = scannerDirs.get_seriesDirs()
    while True:
        selectedSeries = input('Which Series?: ')
        if selectedSeries in seriesDirs:
            break
        else:
            print('{} is not a valid series choice!'.format(selectedSeries))

    # prompt user to specify an output name, and format to remove any spaces
    outputPrefix = input('Output Prefix: ')
    outputPrefix = outputPrefix.replace(' ', '')

    # progress updates
    print('='*5)
    print('Building Nifti...')
    print('\tinput series: {}'.format(selectedSeries))
    print('\toutput name: {}'.format(outputPrefix))

    # get the full path to the series dir
    seriesDir = join(scannerDirs.sessionDir, selectedSeries)

    # create an instance of the Siemens_NiftiBuilder
    niftiBuilder = Philips_BuildNifti(seriesDir)
    print('Successfully built Nifti image...\n')

    # ask user whether they want to save it locally or send
    print('Save nifti locally (1), or Send to remote machine (2)')
    while True:
        saveOrSend = input('type 1 or 2: ')
        if saveOrSend in ['1', '2']:
            break
        else:
            print('{} is not a valid choice!'.format(saveOrSend))

    if saveOrSend == '1':
        output_path = join(pynealScannerDir, 'data', '{}_{}.nii.gz'.format(outputPrefix, selectedSeries))
        niftiBuilder.write_nifti(output_path)

    elif saveOrSend == '2':
        pass


def getSeries_Siemens(scannerSettings, scannerDirs):
    """
    Steps for getting offline data from the scanner that are
    specific to Siemens environments
    """
    from utils.Siemens_utils import Siemens_BuildNifti

    # prompt user to specifiy a series. Make sure that it is a valid
    # series before continuing
    seriesDirs = scannerDirs.get_seriesDirs()
    while True:
        selectedSeries = input('Which Series?: ')
        if selectedSeries in seriesDirs:
            break
        else:
            print('{} is not a valid series choice!'.format(selectedSeries))

    # prompt user to specify an output name, and format to remove any spaces
    outputPrefix = input('Output Prefix: ')
    outputPrefix = outputPrefix.replace(' ', '')

    # progress updates
    print('='*5)
    print('Building Nifti...')
    print('\tinput series: {}'.format(selectedSeries))
    print('\toutput name: {}'.format(outputPrefix))

    # get the full path to the series dir
    seriesDir = join(scannerDirs.sessionDir, selectedSeries)

    # create an instance of the Siemens_NiftiBuilder
    niftiBuilder =Siemens_BuildNifti(seriesDir)
    print('Successfully built Nifti image...\n')

    # ask user whether they want to save it locally or send
    print('Save nifti locally (1), or Send to remote machine (2)')
    while True:
        saveOrSend = input('type 1 or 2: ')
        if saveOrSend in ['1', '2']:
            break
        else:
            print('{} is not a valid choice!'.format(saveOrSend))

    if saveOrSend == '1':
        output_path = join(pynealScannerDir, 'data', '{}_{}.nii.gz'.format(outputPrefix, selectedSeries))
        niftiBuilder.write_nifti(output_path)

    elif saveOrSend == '2':
        pass


if __name__ == '__main__':

    # initialize the session classes:
    scannerSettings, scannerDirs = initializeSession()

    # print all of the current series dirs to the terminal
    scannerDirs.print_seriesDirs()

    # load the appropriate tools for this scanning environment
    scannerMake = scannerSettings.allSettings['scannerMake']
    if scannerMake == 'GE':
        getSeries_GE(scannerSettings, scannerDirs)
    elif scannerMake == 'Philips':
        getSeries_Philips(scannerSettings, scannerDirs)
    elif scannerMake == 'Siemens':
        getSeries_Siemens(scannerSettings, scannerDirs)
    else:
        print('Unrecognized scanner make: {}'.format(scannerMake))
