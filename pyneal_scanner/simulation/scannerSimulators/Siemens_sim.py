""" Simulate a Siemens scan

Siemens scanners export reconstructed volumes by taking all of the
slices for a single volume, and arranging them in a 2D grid as a so-called
"mosaic" dicom image. A scan will produce one mosaic image per volume, and
all mosaic images for all scans across a single session will be stored in the
same directory. This script simulates the creation of that directory, and will
pass in real mosaic images.

Usage:
------
    python Siemens_sim.py inputDir series# [--newSeriesNum] [--TR]

You must specify a local path to the inputDir as well as the series number of
the series you want to simulate.

The input dir should be the directory that already contains a set of
reconstructed mosaic dicom images. Let's call that directory the 'sessionDir'.
A single session dir will hold all of the mosaic files for all of the scans for
a given session. Mosaic files are named like:

<session#>_<series#>_<vol#>.dcm

[OPTIONAL]: You can specify the series number that will be assigned to the
"new" mosaic images. The default behavior is to assign a series number based
on the next sequential number given the existing series. In the example below,
the default would be to assign a newSeriesNum as '2', but we are overriding
that to assign it as '19'

e.g. python Siemens_sim.py /Path/To/My/Existing/SessionDir 1 --newSeriesNum 19

[OPTIONAL]: You can specify the TR at which new slice data is copied. Default
is 1000ms, and represents the approximate amount of time it should take to copy
over all of the slices for one volume of data.

e.g. python Siemens_sim.py /Path/To/My/Existing/SessionDir 1 --TR 2000

"""
# python 2/3 compatibility
from __future__ import print_function
from builtins import input

import os
import sys
from os.path import join
import glob
import argparse
import atexit
import re
import time
import subprocess

# regEx for Siemens style file naming
Siemens_filePattern = re.compile('\d{3}_\d{6}_\d{6}.dcm')
Siemens_mosaicVolumeNumberField = re.compile('(?<=\d{6}_)\d{6}')
Siemens_mosaicSeriesNumberField = re.compile('(?<=\d{3}_)\d{6}(?=_\d{6}.dcm)')


def Siemens_sim(inputDir, seriesNum, newSeriesNum, TR):
    """ Simulate a Siemen scanning environment

    To simulate a scan, this function will read all of mosaic dicom files from
    the specified `inputDir` that have the specified `seriesNum`. Each mosaic
    file will then be duplicated, renamed with the `newSeriesNum`, and then
    saved in the same `inputDir`.

    The rate that each mosaic file is duplicated, renamed, and saved is
    determined by the `TR` parameter

    Parameters
    ----------
    inputDir : string
        full path to directory containing all of the mosaic images for all
        series within the current session
    seriesNum : int
        series number of the series you wish to use for the simulation data
    newSeriesNum : int
        series number to assign to the new simulated data
    TR : int
        the time it takes to copy each volume in the series.
        Units: milliseconds

    """
    # build full path to outputDir
    print('-'*25)
    print('Source dir: {}'.format(inputDir))

    # make a list of mosaic files
    mosaicFiles = {}
    for f in glob.glob(join(inputDir, ('*_' + str(seriesNum).zfill(6) + '_*.dcm'))):
        # parse just the volume number field from file name
        volNum = int(os.path.split(f)[1].split('_')[2][:-4])
        mosaicFiles[volNum] = f

    # print parameters
    print('Total Mosaics Found: {}'.format(len(mosaicFiles)))
    print('TR: {}'.format(TR))

    # convert TR to s
    TRs = TR/1000

    # wait for input to begin
    input('Press ENTER to begin the "scan" ')

    # sleep for one TR to simulation collection of first volume
    time.sleep(TRs)

    # loop over all slice files
    print('copied dicom mosaic #:', end=' ')
    newSeriesNum = str(newSeriesNum).zfill(6)
    for fileIdx in sorted(mosaicFiles, key=int):
        startTime = time.time()

        src_file = join(inputDir, mosaicFiles[fileIdx])

        # build new file name by swapping out seriesNumber field
        dst_file = makeNewFileName(src_file, seriesNum, newSeriesNum)

        # copy the file
        subprocess.call(['cp', src_file, dst_file])
        print(fileIdx, end=', ', flush=True)

        endTime = time.time()
        elapsed = endTime-startTime
        if elapsed < TRs:
            # introduce delay for the remaing TR period
            time.sleep(TRs-elapsed)


def makeNewFileName(srcFile, oldSeriesNum, newSeriesNum):
    """ swap out the oldSeriesNum with the newSeriesNum

    Parameters
    ----------
    srcFile : string
        full path to the source mosaic file
    oldSeriesNum : int
        what the seriesNum currently is
    newSeriesNum : int
        what you want the new series number to be

    Returns
    -------
    string
        full path to the new filename for the series file

    """
    oldSeriesNum = str(oldSeriesNum).zfill(6)
    newSeriesNum = str(newSeriesNum).zfill(6)
    srcDir, origFile = os.path.split(srcFile)

    newFileName = origFile.replace(('_' + oldSeriesNum + '_'),
                                   ('_' + newSeriesNum + '_'))

    newFile = join(srcDir, newFileName)
    return newFile


def rmFiles(seriesDir, seriesNum):
    """ Remove all files with the specified seriesNum from the specified dir

    """
    for f in glob.glob(join(seriesDir, ('*_' + str(seriesNum).zfill(6) + '_*.dcm'))):
        print('Deleting file: {}'.format(f))
        subprocess.call(['rm', f])


if __name__ == "__main__":
    # parse arguments
    parser = argparse.ArgumentParser(description='Simulate a Siemens scan')
    parser.add_argument('inputDir',
                        help='path to directory that contains mosaic DICOMS')
    parser.add_argument('seriesNum',
                        help='seriesNum of scan you want to simulate')
    parser.add_argument('-n', '--newSeriesNum',
                        default=None,
                        help='new series number to assign to copied data [default: use sequential numbering])')
    parser.add_argument('-t', '--TR',
                        type=int,
                        default=1000,
                        help='TR (ms) [default = 1000ms]')

    # grab the input args
    args = parser.parse_args()

    # check if input dir is valid
    if not os.path.isdir(args.inputDir):
        print('Invalid input dir: {}').format(args.inputDir)
        sys.exit()

    # check to make sure the specifed series number exists in the dir
    seriesFiles = glob.glob(join(args.inputDir,
                            ('*_' + str(args.seriesNum).zfill(6) + '_*.dcm')))
    if len(seriesFiles) == 0:
        print('No scans with seriesNum {} were found'.format(args.seriesNum))
        sys.exit()

    # figure out existing series nums
    seriesNums = []
    for f in glob.glob(join(args.inputDir, '*.dcm')):
        seriesNums.append(int(os.path.split(f)[1].split('_')[1]))
    uniqueSeries = set(seriesNums)

    # set the newSeriesNum
    if args.newSeriesNum is not None:
        if args.newSeriesNum in uniqueSeries:
            newSeriesNum = max(uniqueSeries) + 1
            print('the newSeriesNum you specifed already exists...using {}'.format(newSeriesNum))
        else:
            newSeriesNum = args.newSeriesNum
    else:
        newSeriesNum = max(uniqueSeries) + 1

    # set up the cleanup function
    atexit.register(rmFiles, args.inputDir, newSeriesNum)

    # run main function
    Siemens_sim(args.inputDir, args.seriesNum, newSeriesNum, args.TR)
