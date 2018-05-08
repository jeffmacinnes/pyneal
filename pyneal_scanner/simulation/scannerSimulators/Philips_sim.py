"""
Simulate a Philips scan
Philips scanners use XTC (eXTernal Control) to output reconstructed volumes during
a scan. The files are written to a designated directory (e.g. XTC_Output), and
within that directory, every series is assigned a new directory named sequentially
starting with '0000'. For instance, volumes from the 3rd series will be stored
like '.../XTC_Output/0002/'. This script will simulate the creation of a new series
directory, and copy in PAR/REC files.

Usage:
    python Philips_sim.py inputDir [--outputDir] [--TR]

You must specify a local path to the inputDir. That is, the directory that already
contains a set of reconstructed PAR/REC files for a series. Let's call this directory
the seriesDir. Everything in the path up to the seriesDir we'll call the sessionDir.
So, your input PAR/REC files are stored somewhere like:

<sessionDir>/<seriesDir>/

To use this tool, you must specify an inputDir as the full path (i.e. <sessionDir>/<seriesDir>)
to the source data.

[OPTIONAL]: You can specify the full path to an output directory where the PAR/REC files
will be copied to. If you don't specify an output directory, this tool will default
to creating a new seriesDir, named '9999' in the sessionDir.

e.g. python Philips_sim.py /Path/To/My/Existing/Series/0000 --outputDir /Where/I/Want/New/Slice/Data/To/appear

if you did not specify an outputDir, new PAR/RECs would be copied to:

/Path/To/My/Existing/Series/9999

[OPTIONAL]: You can specify the TR at which new PAR/REC data is copied.
Default is 1000ms.

e.g. python GE_sim.py /Path/To/My/Existing/Series/0000 --TR 2000
"""
# python 2/3 compatibility
from __future__ import print_function
from builtins import input

import os, sys
from os.path import join
import argparse
import atexit
import glob
import time
import subprocess

import nibabel as nib


def Philips_sim(inputDir, outputDir, TR):
    """
    Transfer PAR/REC pairs in order from the inputDir to the outputDir
    at a rate set by the TR
    """
    # build full path to outputDir
    print('-'*25)
    print('Source slices: {}'.format(inputDir))
    print('Output dir: {}'.format(outputDir))

    # if the outputDir exists, delete
    if os.path.isdir(outputDir):
        print('Deleting existing {}'.format(outputDir))
        subprocess.call(['rm', '-r', outputDir])

    # make a list of all of the volume files (ony do .PAR files)
    parFiles = glob.glob(join(inputDir, 'Dump-*.par'))

    # print parameters
    print('Total Volumes: ', len(parFiles))
    print('TR: ', TR)

    # wait for input to begin
    input('Press ENTER to begin the "scan" ')

    # create the outputDir
    os.makedirs(outputDir)

    # Loop over all volume files (Note: vols are assumed to be named sequentially)
    print('copied volume #: ', end=' ')
    for i,v in enumerate(sorted(parFiles)):
        timeStart = time.time()

        # copy par file
        p, par_fname = os.path.split(v)
        src_par = join(inputDir, par_fname)
        dst_par = join(outputDir, par_fname)
        subprocess.call(['cp', src_par, dst_par])

        # copy the rec file
        rec_fname = par_fname.split('.')[0] + '.rec'
        src_rec = join(inputDir, rec_fname)
        dst_rec = join(outputDir, rec_fname)
        subprocess.call(['cp', src_rec, dst_rec])

        # print progress update
        print(i, end=', ', flush=True)

        # sleep for remaining part of TR
        elapsedTime = time.time()-timeStart
        if elapsedTime < (TR/1000):
            time.sleep((TR/1000)-elapsedTime)



def rmOutputDir(outputDir):
    """ Remove the output dir upon exiting"""
    # if outputDir exists, delete
    if os.path.isdir(outputDir):
        print('Deleting output dir: {}'.format(outputDir))
        subprocess.call(['rm', '-r', outputDir])


if __name__ == "__main__":
    # parse arguments
    parser = argparse.ArgumentParser(description='Simulate a Philips Scan')
    parser.add_argument('inputDir',
                help='path to directory contains PAR/RECs for the series you want to simulate')
    parser.add_argument('-o', '--outputDir',
                default=None,
                help='path to output directory where new slice images will appear (i.e. new seriesDir)')
    parser.add_argument('-t', '--TR',
                type=int,
                default=1000,
                help='TR(ms) [default = 1000ms]')

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
        defaultNewDir = '0999'
        outputDir = join(sessionDir, defaultNewDir)
    else:
        outputDir = args.outputDir

    # set up the cleanup function
    atexit.register(rmOutputDir, outputDir)

    # run main function
    Philips_sim(args.inputDir, outputDir, args.TR)
