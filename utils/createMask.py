""" Tool to create masks to be used during a real-time run.

*REQUIRES FSL 5.0+*

The mask MUST match the dimensions and orientation of incoming functional data.
That is, the mask must be in subject functional space.

This tool will transform a selected MNI space mask to subject functional space.
To do so, you must supply:
    - example functional space data from the current subject. This can be a
    a short functional run (~15s) that you've already collected
    - a high resolution anatomical image from the current subject
    - the MNI space mask you wish to transform

Using FSL FLIRT, this tool will create the intermediary transforms to map from
MNI-to-HIRES, and HIRES-to-FUNC space, and then combine the transformation
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
import logging
import subprocess

import yaml

# set the Pyneal root dir. Assumes this tool lives in .../pyneal/utils/
# pynealDir must be set and added to the path in order to import GUI
utilsDir = os.path.abspath(os.path.dirname(__file__))
pynealDir = os.path.dirname(utilsDir)
sys.path.insert(0, pynealDir)
import src.GUIs.createMask.createMaskGUI as createMaskGUI


class MaskCreator():
    """ Mask Creator module

    This class contains functions for creating transformation matrices for
    mapping between various image spaces, based on inputs provided in the
    settings file. These transformations can be used to create new masks.

    """
    def __init__(self):
        """ Initialize the class

        Open GUI to modify settings file. Read settings. Create logfiles
        and necessary output directories. Make masks accordingly

        """
        ### Read Settings ------------------------------------
        # Read the settings file, and launch the createMask GUI to give the user
        # a chance to update the settings. Hitting 'submit' within the GUI
        # will update the createMaskConfig file with the new settings
        settingsFile = join(pynealDir, 'src/GUIs/createMask/createMaskConfig.yaml')

        # Launch GUI
        createMaskGUI.launchCreateMaskGUI(settingsFile)

        # start the timer
        startTime = time.time()

        # Read the new settings file, store as dict
        with open(settingsFile, 'r') as ymlFile:
            self.settings = yaml.load(ymlFile, Loader=yaml.FullLoader)

        ### Setup output dirs and logging
        self.outputDir = join(os.path.dirname(self.settings['subjFunc']), 'mask_transforms')
        if not os.path.isdir(self.outputDir):
            os.makedirs(self.outputDir)
        self.logger = createLogger(join(self.outputDir, 'maskTransforms.log'))

        # write settings to log
        for s in self.settings:
            self.logger.debug('Settings: {}: {}'.format(s, self.settings[s]))

        ### Average func data to create an example 3D func image
        self.logger.info('creating exampleFunc image by averaging input func and running brain extraction')
        outputFile = join(self.outputDir, 'exampleFunc.nii.gz')
        if not exists(outputFile):
            # average func file
            cmdList = ['fslmaths', self.settings['subjFunc'], '-Tmean', outputFile]
            self.logger.debug(' '.join(cmdList))
            subprocess.call(cmdList)

            # run Brain Extraction Tool, overwriting output from previous step
            cmdList = ['bet', outputFile, outputFile, '-f', '0.4', '-g', '0']
            self.logger.debug(' '.join(cmdList))
            subprocess.call(cmdList)
        else:
            self.logger.info('using existing: {}'.format(outputFile))

        ### Create func space whole brain mask, if specified
        if self.settings['createFuncBrainMask']:
            self.createFuncBrainMask()

        ### Transform MNI-space mask to func space, if specified
        if self.settings['transformMaskToFunc']:
            self.transformMaskToFunc()

        ### Calculate total time
        elapsedTime = time.time() - startTime
        self.logger.info('Total processing time: {:.3f} seconds'.format(elapsedTime))

        ### Display all masks in fslEyes
        self.displayMasks()

    def createMaskOutputDir(self):
        """ Create output directory for saving functional-space masks

        Create a subdir in the mask_transforms directory that holds all of the
        completed masks, transformed to subject FUNC space

        """
        self.maskOutputDir = join(self.outputDir, 'FUNC_masks')
        if not os.path.isdir(self.maskOutputDir):
            os.makedirs(self.maskOutputDir)

    def createFuncBrainMask(self):
        """ Create a whole brain mask of the example functional data

        """
        # make sure mask output dir exists
        self.createMaskOutputDir()

        # specify path to example func image
        exampleFunc = join(self.outputDir, 'exampleFunc.nii.gz')
        self.logger.info('creating whole brain mask from: {}'.format(exampleFunc))

        # run fsl bet command to create whole brain mask
        outputFile = join(self.maskOutputDir, 'wholeBrain_FUNC')
        cmdList = ['bet', exampleFunc, outputFile, '-n', '-m']
        self.logger.debug(' '.join(cmdList))
        subprocess.call(cmdList)

        self.logger.info('created func brain mask: {}'.format(outputFile))

    def transformMaskToFunc(self):
        """ Transform the chosen MNI space mask to functional space

        """
        # make sure mask output dir exists
        self.createMaskOutputDir()

        self.logger.info('transforming MNI mask to functional space')

        ###  - brain extraction on the hi-res anat image, if specified
        outputFile = join(self.outputDir, 'hires_brain.nii.gz')
        if self.settings['skullStrip']:
            self.logger.info('skull stripping hi-res subject anatomical')
            if not exists(outputFile):
                cmdList = ['bet', self.settings['subjAnat'], outputFile, '-f', '0.35']
                self.logger.debug(' '.join(cmdList))
                subprocess.call(cmdList)
            else:
                self.logger.info('using existing: {}'.format(outputFile))
        else:
            self.logger.info('copying {} to {}'.format(self.settings['subjAnat'], outputFile))
            cmdList = ['cp', self.settings['subjAnat'], outputFile]
            self.logger.debug(' '.join(cmdList))
            subprocess.call(cmdList)

        ### register MNI standard --> hires
        self.logger.info('creating mni2hires transformation matrix')
        outputFile = join(self.outputDir, 'mni2hires.mat')
        if not exists(outputFile):
            cmdList = ['flirt', '-in', self.settings['MNI_standard'],
                       '-ref', join(self.outputDir, 'hires_brain.nii.gz'),
                       '-out', join(self.outputDir, 'mni_HIRES'),
                       '-omat', outputFile,
                       '-bins', '256', '-cost', 'corratio',
                       '-searchrx', '-180', '180',
                       '-searchry', '-180', '180',
                       '-searchrz', '-180', '180',
                       '-dof', '9', '-interp', 'trilinear']
            self.logger.debug(' '.join(cmdList))
            subprocess.call(cmdList)
        else:
            self.logger.info('using existing: {}'.format(outputFile))

        ### register hires --> functional space
        self.logger.info('creating hires2func transformation matrix')
        outputFile = join(self.outputDir, 'hires2func.mat')
        if not exists(outputFile):
            cmdList = ['flirt', '-in', join(self.outputDir, 'hires_brain.nii.gz'),
                       '-ref', join(self.outputDir, 'exampleFunc.nii.gz'),
                       '-out', join(self.outputDir, 'hires_FUNC'),
                       '-omat', outputFile,
                       '-bins', '256', '-cost', 'corratio',
                       '-searchrx', '-90', '90',
                       '-searchry', '-90', '90',
                       '-searchrz', '-90', '90',
                       '-dof', '9', '-interp', 'trilinear']
            self.logger.debug(' '.join(cmdList))
            subprocess.call(cmdList)
        else:
            self.logger.info('using existing: {}'.format(outputFile))

        ### concatenate mni2hires and hires2func to create mni2func transform
        self.logger.info('concatenating mni2hires and hires2func matrices')
        outputFile = join(self.outputDir, 'mni2func.mat')
        if not exists(outputFile):
            # Note that the transform after '-concat' should be 2nd transform you want applied
            cmdList = ['convert_xfm', '-omat', outputFile,
                       '-concat', join(self.outputDir, 'hires2func.mat'),
                       join(self.outputDir, 'mni2hires.mat')]
            self.logger.debug(' '.join(cmdList))
            subprocess.call(cmdList)
        else:
            self.logger.info('using existing: {}'.format(outputFile))

        ### apply mni2func transform to the chosen mask; this will create the weighted version of
        # mask in subject functional space
        self.logger.info('applying mni2func transform to {}'.format(self.settings['MNI_mask']))
        self.weightedMaskPath = join(self.maskOutputDir, (self.settings['outputPrefix'] + '_FUNC_weighted'))
        cmdList = ['flirt', '-in', self.settings['MNI_mask'],
                   '-ref', join(self.outputDir, 'exampleFunc.nii.gz'),
                   '-out', self.weightedMaskPath,
                   '-applyxfm', '-init', join(self.outputDir, 'mni2func.mat'),
                   '-interp', 'trilinear']
        self.logger.debug(' '.join(cmdList))
        subprocess.call(cmdList)

        ### binarize the weighted FUNC space mask
        self.logger.info('creating binarized mask of {}'.format(self.weightedMaskPath))
        self.binarizedMaskPath = self.weightedMaskPath.replace('FUNC_weighted', 'FUNC_mask')
        cmdList = ['fslmaths', self.weightedMaskPath, '-bin', self.binarizedMaskPath]
        self.logger.debug(' '.join(cmdList))
        subprocess.call(cmdList)

    def displayMasks(self):
        """ Display masks in fsleyes

        Display all masks in fsleyes. If transformMaskToFunc selected, use the
        hires_FUNC (high-res anatomical transformed to FUNC space) as the
        background layer, otherwise exampleFunc

        """
        # figure out appropriate BG image
        if self.settings['transformMaskToFunc']:
            cmd = ['fsleyes', join(self.outputDir, 'hires_FUNC.nii.gz')]
        else:
            cmd = ['fsleyes', join(self.outputDir, 'exampleFunc.nii.gz')]

        # add whole brain mask, if specified
        if self.settings['createFuncBrainMask']:
            cmd.append(join(self.maskOutputDir, 'wholeBrain_FUNC_mask.nii.gz'))
            cmd.append('-cm')
            cmd.append('yellow')

        # add the transformed masks (weighted and binarized both), if specified
        if self.settings['transformMaskToFunc']:
            cmd.append(join(self.maskOutputDir, (self.settings['outputPrefix'] + '_FUNC_mask.nii.gz')))
            cmd.append('-cm')
            cmd.append('red')

            cmd.append(join(self.maskOutputDir, (self.settings['outputPrefix'] + '_FUNC_weighted.nii.gz')))
            cmd.append('-cm')
            cmd.append('hot')

        # call the fsleyes cmd
        subprocess.call(cmd)


def createLogger(logName):
    """ Create logger for storing log messages pertaining to creating new
    masks

    """
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
    m = MaskCreator()
