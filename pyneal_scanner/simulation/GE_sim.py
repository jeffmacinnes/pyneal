"""
Simulate a GE scan

GE scanners store reconstructed slice images as individual DICOM files within
a certain directory on the scanner console. This script will simulate that directory
and pass in individual slice DICOM images.

You must specify a local path to a directory that already contains a set of reconstructed
GE slice DICOMS. Within that directory, this script will create a new directory called "scanned"
and prompt you to start the simulation. Once you press [RETURN], slice images will be copied into
the new directory.

"""
# python 2/3 compatibility
from __future__ import print_function
from builtins import input

import os, sys
from os.path import join
import argparse
import re
import time
import dicom
import subprocess

# regEx for GE style file naming
GE_filePattern = re.compile('i\d*.MRDC.\d*')


def GE_sim(dicomDir, outputDir, TR):
    """
    Read DICOM slices from 'dicomDir',
    copy to outputDir at a rate set by TR
    """
    # build full path to outputDir
    outputDir = join(dicomDir, outputDir)
    print('-'*25)
    print('Output saved to: ', outputDir)


    # if outputDir exists, delete
    if os.path.isdir(outputDir):
        print('Deleting existing {}'.format(outputDir))
        subprocess.call(['rm', '-r', outputDir])
        #shutil.rmtree(outputDir)

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

if __name__ == "__main__":
    # parse arguments
    parser = argparse.ArgumentParser()
    parser.add_argument('dicomDir',
                help='path to directory that contains slice DICOMS')
    parser.add_argument('-o', '--outputDir',
                default='s100',
                help='name of output directory where new slices images will appear (i.e. series directory) [default: s100]')
    parser.add_argument('-t', '--TR',
                type=int,
                default=2000,
                help='TR, how quickly to transfer the slices comprising 1 volume (ms) [default: 2000]')

    # grab the input args
    args = parser.parse_args()

    # check if input dir is valid
    if not os.path.isdir(args.dicomDir):
        print('Invalid input dir: {}').format(args.dicomDir)
        sys.exit()
    else:
        # run main function
        GE_sim(args.dicomDir, args.outputDir, args.TR)
