"""
Simulate a GE scan [GE MR750 3T].
GE scanners store reconstructed slice images as individual DICOM files within
a certain directory on the scanner console. This script will simulate that directory
and copy in individual slice DICOM images.

Usage:
    python GE_sim.py inputDir [--outputDir] [--TR]

You must specify a local path to the inputDir. That is, the directory that already
contains a set of reconstructed GE slice DICOMS. Let's call directory the seriesDir. Everything in the path up to the seriesDir
we'll call the sessionDir. So, your input slice data is stored somewhere like:

<sessionDir>/<seriesDir>/

To use this tool, you must specify an inputDir as the full path (i.e. <sessionDir>/<seriesDir>) to
the source data.

[OPTIONAL]: You can specify the full path to an output directory where the slices
will be copied to. If you don't specify an output directory, this tool will default
to creating a new seriesDir, named 's9999' in the sessionDir.

e.g. python GE_sim.py /Path/To/My/Existing/Slice/Data --outputDir /Where/I/Want/New/Slice/Data/To/appear

if you did not specify an outputDir, new slices would be copied to:

/Path/To/My/Existing/Slice/s9999

[OPTIONAL]: You can specify the TR at which new slice data is copied. Default is 1000ms, and
represents the approximate amount of time it should take to copy over all of the slices for
one volume of data.

e.g. python GE_sim.py /Path/To/My/Existing/Slice/Data --TR 2000

"""
# python 2/3 compatibility
from __future__ import print_function
from builtins import input

import os, sys
from os.path import join
import argparse
import atexit
import re
import time
import subprocess

import dicom

# regEx for GE style file naming
GE_filePattern = re.compile('i\d*.MRDC.\d*')


def GE_sim(dicomDir, outputDir, TR):
    """
    Read DICOM slices from 'dicomDir',
    copy to outputDir at a rate set by TR
    """

    # build full path to outputDir
    print('-'*25)
    print('Source slices: {}'.format(dicomDir))
    print('Output dir: {}'.format(outputDir))

    # if outputDir exists, delete
    if os.path.isdir(outputDir):
        print('Deleting existing {}'.format(outputDir))
        subprocess.call(['rm', '-r', outputDir])

    # make a list of slice files
    sliceFiles = []
    for f in os.listdir(dicomDir):
        if GE_filePattern.match(f):
            sliceFiles.append(f)

    # read one slice to get TR and # of slices/vol info
    ds = dicom.read_file(join(dicomDir, sliceFiles[0]))
    slicesPerVol = ds.ImagesInAcquisition

    # calculate delay between slices
    sliceDelay = TR/slicesPerVol/1000

    # print parameters
    print('Total Slices Found: ', len(sliceFiles))
    print('TR: ', TR)
    print('slices per vol:', slicesPerVol)
    print('delay between slices:', sliceDelay)

    # wait for input to begin
    input('Press ENTER to begin the "scan" ')

    # create the outputDir:
    os.makedirs(outputDir)

    # loop over all slice files
    print('copied dicom #:', end=' ')
    for f in sliceFiles:
        dicomNumber = f.split('.')[-1]
        src_file = join(dicomDir, f)
        dst_file = join(outputDir, f)

        # copy the file
        subprocess.call(['cp', src_file, dst_file])
        print(dicomNumber, end=', ', flush=True)

        # introduce delay
        time.sleep(sliceDelay)


def rmOutputDir(outputDir):
    """ Remove the output dir upon exiting"""
    # if outputDir exists, delete
    if os.path.isdir(outputDir):
        print('Deleting output dir: {}'.format(outputDir))
        subprocess.call(['rm', '-r', outputDir])



if __name__ == "__main__":
    # parse arguments
    parser = argparse.ArgumentParser(description='Simulate a GE scan')
    parser.add_argument('inputDir',
                help='path to directory that contains slice DICOMS')
    parser.add_argument('-o', '--outputDir',
                default=None,
                help='path to output directory where new slices images will appear (i.e. series directory)')
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

    # check if the output Dir is specified. If not, create it
    if args.outputDir is None:
        # strip trailing slash, if present
        if args.inputDir[-1] == os.sep:
            args.inputDir = args.inputDir[:-1]
        sessionDir, seriesDir = os.path.split(args.inputDir)
        defaultNewDir = 's9999'
        outputDir = join(sessionDir, defaultNewDir)
    else:
        outputDir = args.outputDir

    # set up the cleanup function
    atexit.register(rmOutputDir, outputDir)

    # run main function
    GE_sim(args.inputDir, outputDir, args.TR)
