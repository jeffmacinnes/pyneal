"""
Tool to create a mask for use during a real-time run.

*REQUIRES FSL 5.0+*

The mask MUST match the dimensions and orientation of incoming functional data.
That is, the mask must be in subject functional space.

This tool will transform a selected MNI space mask to subject functional space.
To do so, you must supply:
    - example functional space data from the current subject. This can be a
    a short functional run (~15s) that you've already collected
    - a high resolution anatomical image from the current subject
    - the MNI space mask you wish to transform

Using FSL FLIRT, this tool will create the intermediary transforms to map from MNI-to-HIRES, and HIRES-to-FUNC space, and then combine the transformation
matrices to produce a transform that maps from MNI-to-FUNC. This transformation
will be applied to the specified MNI-space mask or atlas, producing both
binarized and non-binarized versions of the functional space mask.

Lastly, FSLeyes will open and display the results masks for review.

All output will be saved in a subdirectory called 'mask_transforms' located in
the same directory as the example functional space data
"""

import sys
import os
from os.path import join
from os.path import exists
import time
import shutil
import logging
import subprocess

import yaml

# set the Pyneal root dir. Assumes this tool lives in .../pyneal/utils/
utilsDir = os.path.abspath(os.path.dirname(__file__))
pynealDir = os.path.dirname(utilsDir)

def launchCreateMask():
    """
    Open GUI to modify settings file. Read settings. Build mask accordingly
    """
    startTime = time.time()
    ### Read Settings ------------------------------------
    # Read the settings file, and launch the createMask GUI to give the user
    # a chance to update the settings. Hitting 'submit' within the GUI
    # will update the createMaskConfig file with the new settings
    settingsFile = join(utilsDir, 'createMaskConfig.yaml')

    # Launch GUI
    # TODO

    # Read the new settings file, store as dict
    with open(settingsFile, 'r') as ymlFile:
        settings = yaml.load(ymlFile)

    ### Setup output dir and logging
    outputDir = join(os.path.dirname(settings['subjFunc']), 'mask_transforms')
    if not os.path.isdir(outputDir):
        os.makedirs(outputDir)
    logger = createLogger(join(outputDir, 'maskTransforms.log'))

    # write settings to log
    for s in settings:
        logger.debug('Settings: {}: {}'.format(s, settings[s]))

    ### Copy input files into 'originals' subdirectory
    # create originals directory
    originalsDir = join(outputDir, 'originals')
    if not os.path.isdir(originalsDir):
        os.makedirs(originalsDir)

    for f in ['subjFunc', 'subjAnat']:
        if not exists(join(originalsDir, (f + '.nii.gz'))):
            shutil.copyfile(settings[f], join(originalsDir, (f + '.nii.gz')))

    ### 1 - average functional data to create an example 3D func image
    logger.info('(1/8) ---- creating exampleFunc image by averaging input func')
    outputFile = join(outputDir, 'exampleFunc.nii.gz')
    if not exists(outputFile):
        subprocess.call(['fslmaths', settings['subjFunc'], '-Tmean', outputFile])
    else:
        logger.info('using existing: {}'.format(outputFile))


    ### 2 - brain extraction on the hi-res anat image
    logger.info('(2/8) ---- skull stripping hi-res subject anatomical')
    outputFile = join(outputDir, 'hires_brain.nii.gz')
    if not exists(outputFile):
        subprocess.call(['bet', settings['subjAnat'], outputFile, '-f', '0.35'])
    else:
        logger.info('using existing: {}'.format(outputFile))


    ### 3 - register MNI standard --> hires
    logger.info('(3/8) ---- creating mni2hires transformation matrix')
    outputFile = join(outputDir, 'mni2hires.mat')
    if not exists(outputFile):
        subprocess.call(['flirt', '-in', settings['MNI_standard'],
                        '-ref', join(outputDir, 'hires_brain.nii.gz'),
                        '-out', join(outputDir, 'mni_HIRES'),
                        '-omat', outputFile,
                        '-bins', '256', '-cost', 'corratio',
                        '-searchrx', '-180', '180',
                        '-searchry', '-180', '180',
                        '-searchrz', '-180', '180',
                        '-dof', '9', '-interp', 'trilinear'])
    else:
        logger.info('using existing: {}'.format(outputFile))


    ### 4 - register hires --> functional space
    logger.info('(4/8) ---- creating hires2func transformation matrix')
    outputFile = join(outputDir, 'hires2func.mat')
    if not exists(outputFile):
        subprocess.call(['flirt', '-in', join(outputDir, 'hires_brain.nii.gz'),
                        '-ref', settings['subjFunc'],
                        '-out', join(outputDir, 'hires_FUNC'),
                        '-omat', outputFile,
                        '-bins', '256', '-cost', 'corratio',
                        '-searchrx', '-90', '90',
                        '-searchry', '-90', '90',
                        '-searchrz', '-90', '90',
                        '-dof', '9', '-interp', 'trilinear'])
    else:
        logger.info('using existing: {}'.format(outputFile))


    ### 5 - concatenate mni2hires and hires2func to create mni2func transform
    logger.info('(5/8) ---- concatenating mni2hires and hires2func matrices')
    outputFile = join(outputDir, 'mni2func.mat')
    if not exists(outputFile):
        # Note that the transform after '-concat' should be 2nd transform you want applied
        subprocess.call(['convert_xfm', '-omat', outputFile,
                        '-concat', join(outputDir, 'hires2func.mat'), join(outputDir, 'mni2hires.mat')])
    else:
        logger.info('using existing: {}'.format(outputFile))


    ### 6 - apply mni2func transform to the chosen mask
    logger.info('(6/8) ---- applying mni2func transform to {}'.format(settings['MNI_mask']))
    outputFile = join(outputDir, (settings['outputPrefix'] + '_FUNC_weighted'))
    subprocess.call(['flirt', '-in', settings['MNI_mask'],
                    '-ref', join(outputDir, 'exampleFunc.nii.gz'),
                    '-out', outputFile,
                    '-applyxfm', '-init', join(outputDir, 'mni2func.mat'),
                    '-interp', 'trilinear'])







def createLogger(logName):
    ### FILE HANDLER - set up how log messages should be formatted in the log file
    fileLogger = logging.FileHandler(logName, mode='a')
    fileLogger.setLevel(logging.DEBUG)
    fileLogFormat = logging.Formatter('%(asctime)s - %(levelname)s - : %(message)s', '%m-%d %H:%M:%S')
    fileLogger.setFormatter(fileLogFormat)

    ### CONSOLE HANDLER - set up how log messages should appear in std.Out of the console
    consoleLogger = logging.StreamHandler(sys.stdout)
    consoleLogger.setLevel(logging.INFO)
    consoleLogFormat = logging.Formatter('%(message)s')
    consoleLogger.setFormatter(consoleLogFormat)

    ### ROOT LOGGER, add handlers.
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)
    logger.addHandler(fileLogger)
    logger.addHandler(consoleLogger)

    return logger



if __name__ == '__main__':
    launchCreateMask()
