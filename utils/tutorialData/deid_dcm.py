"""
De-identify dicom files
"""

import os
from os.path import join
import argparse
import glob

import pydicom

# remove the following fields from the dicom headers
fields = ['ReferringPhysicianName',
 'StudyDate',
 'SeriesDate',
 'AcquisitionDate',
 'ContentDate',
 'StudyTime',
 'SeriesTime',
 'AcquisitionTime',
 'ContentTime',
 'StationName',
 'StudyDescription',
 'Image actual date',
 'PatientName',
 'PatientID',
 'PatientBirthDate',
 'PatientSex',
 'PatientAge',
 'PatientWeight',
'ProtocolName']


def deidDcm(inputFiles, outputDir):
    """
    de-identify all of the files in the inputFiles list, write
    as new files in the outputDir
    """
    for i in inputFiles:
        # load each dicom file
        dcm = pydicom.read_file(i)

        # first, remove private tags
        dcm.remove_private_tags

        # loop through all specified dicom fields
        for f in fields:
            if f in dcm:                # check if it exists
                tag = dcm.data_element(f).tag   # get the tag
                dcm[tag].value = ''           # write blank string to field

        # save the deidentified file
        fpath, fname = os.path.split(i)
        new_fname = join(outputDir, fname)
        dcm.save_as(new_fname)


if __name__ == '__main__':
        parser = argparse.ArgumentParser(
                                formatter_class=argparse.ArgumentDefaultsHelpFormatter)
        parser.add_argument('-i', '--inputDir',
                            nargs=1, help='input directory containing dcm files')
        parser.add_argument('-o', '--outputDir',
                            nargs=1, help='output directory to save de-id files to')

        args = parser.parse_args()

        ### Make a list of all of the dicom files in the specified input dir
        inputDir = args.inputDir[0]
        outputDir = args.outputDir[0]
        dicom_files = [os.path.abspath(join(inputDir,f)) for f in os.listdir(inputDir) if os.path.isfile(join(inputDir, f))]

        deidDcm(dicom_files, outputDir)
