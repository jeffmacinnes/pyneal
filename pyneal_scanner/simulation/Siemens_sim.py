"""
Simulate a Siemens scan [Siemens Prisma 3T]
Siemens scanners stores reconstructed slices images by taking all of the
slices for a single volume, and placing them side-by-side in a larger
"mosaic" dicom image. A scan will produce one mosaic image per volume, and
all mosaic images for a given scan will be stored in the same directory. This
script simulates the creation of that directory, and will pass in real
mosaic images.

Usage:
    python Siemens_sim.py inputDir [--outputDir] [--TR]

You must specify a local path to the inputDir. That is, the directory that
already contains a set of reconstructed mosaic images for a given scan. Let's
call that directory the 'seriesDir'. Everything in the path up to that directory
we'll call the 'sessionDir'. So, your input mosaic images are stored somewhere
like:

<sessionDir>/<seriesDir>

[FILL IN MORE INFO ONCE WE KNOW HOW SIEMENS DIRECTORIES ARE STORED]

[OPTIONAL]: You can specify the TR at which new slice data is copied. Default is
1000ms, and represents the approximate amount of time it should take to copy
over all of the slices for one volume of data.

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

# regEx for Siemens style mosaic file naming
Siemens_filePattern = re.compile('RESEARCH.*.MR.PRISMA_HEAD.*')


def Siemens_sim(dicomDir, outputDir, TR):
    """
    Read DICOM mosaics from 'dicomDir',
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

    # make a list of mosaic files
    mosaicFiles = []
    for f in os.listdir(dicomDir):
        if Siemens_filePattern.match(f):
            mosaicFiles.append(f)

    # print parameters
    print('Total Mosaics Found: {}'.format(len(mosaicFiles)))
    print('TR: {}'.format(TR))

    # convert TR to s
    TRs = TR/1000

    # wait for input to begin
    input('Press ENTER to begin the "scan" ')

    # create the outputDir:
    os.makedirs(outputDir)

    # loop over all slice files
    print('copied dicom mosaic #:', end=' ')
    for f in mosaicFiles:
        startTime = time.time()

        dicomNumber = f.split('.')[-10]
        src_file = join(dicomDir, f)
        dst_file = join(outputDir, f)

        # copy the file
        subprocess.call(['cp', src_file, dst_file])
        print(dicomNumber, end=', ', flush=True)

        endTime = time.time()
        elapsed = endTime-startTime
        if elapsed < TRs:
            # introduce delay for the remaing TR period
            time.sleep(TRs-elapsed)


def rmOutputDir(outputDir):
    """ Remove the output dir upon exiting"""
    # if outputDir exists, delete
    if os.path.isdir(outputDir):
        print('Deleting output dir: {}'.format(outputDir))
        subprocess.call(['rm', '-r', outputDir])


if __name__ == "__main__":
    # parse arguments
    parser = argparse.ArgumentParser(description='Simulate a Siemens scan')
    parser.add_argument('inputDir',
                help='path to directory that contains mosaic DICOMS')
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

    # check if the outputDir is specified. If not, create it
    if args.outputDir is None:
        # strip trailing slash, if present
        if args.inputDir[-1] == os.sep:
            args.inputDir = args.inputDir[:-1]
        sessionDir, seriesDir = os.path.split(args.inputDir)
        defaultNewDir = 'series0999'
        outputDir = join(sessionDir, defaultNewDir)
    else:
        outputDir = args.outputDir

    # set up the cleanup function
    atexit.register(rmOutputDir, outputDir)

    # run main function
    Siemens_sim(args.inputDir, outputDir, args.TR)
