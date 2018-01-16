"""
Pyneal Real-time fMRI Acquisition and Analysis

This is the main Pyneal application, designed to be called directly from the
command line on the computer designated as your real-time analysis machine.
It expects to receive incoming slice data from the Pyneal-Scanner application,
which should be running concurrently elsewhere (e.g. on the scanner console
itself)

Once this application is called, it'll take care of opening the
GUI, loading settings, launching separate threads for monitoring and analyzing
incoming data, and hosting the Analysis output server
"""
# python 2/3 compatibility
from __future__ import print_function

import os
import sys
from os.path import join
import time

import yaml
import nibabel as nib
import numpy as np

from src.scanReceiver import ScanReceiver
from src.pynealLogger import createLogger
from src.pynealPreprocessing import Preprocessor
from src.pynealAnalysis import Analyzer
import src.GUIs.pynealSetup.setup as setupGUI

# Set the Pyneal Root dir based on where this file lives
pynealDir = os.path.abspath(os.path.dirname(__file__))

def launchPyneal():
    """
    Main Pyneal Loop. This function will launch setup GUI,
    retrieve settings, initialize all threads, and start processing
    incoming scans
    """
    ### Set Up Logging ------------------------------------
    # The createLogger function will do a lot of the formatting set up
    # behind the scenes. You can write to this log by calling the
    # logger var and specifying the level, e.g.: logger.debug('msg')
    # Other modules can write to this same log by calling
    # logger = logging.getLogger('PynealLog')
    logFname = join(pynealDir, 'logs/pynealLog.log')
    logger = createLogger(logFname)


    ### Read Settings ------------------------------------
    # Read the settings file, and launch the setup GUI to give the user
    # a chance to update the settings. Hitting 'submit' within the GUI
    # will update the setupConfig file with the new settings
    settingsFile = join(pynealDir,'src/setupConfig.yaml')

    # Launch GUI to let user update the settings file
    setupGUI.launchPynealSetupGUI(settingsFile)

    # Read the new settings file, store as dict, write to log
    with open(settingsFile, 'r') as ymlFile:
        settings = yaml.load(ymlFile)
    for k in settings:
        logger.debug('Setting: {}: {}'.format(k, settings[k]))




    ### Launch Threads -------------------------------------
    # Scan Receiver Thread, listens for incoming volume data, builds matrix
    scanReceiver = ScanReceiver(numTimepts=settings['numTimepts'],
                                port=settings['scannerPort'])
    scanReceiver.daemon = True
    scanReceiver.start()
    logger.debug('Starting Scan Receiver')


    ### Create processing objects --------------------------
    # Load the mask
    mask_img = nib.load(settings['maskFile'])

    # Class to handle all preprocessing
    preprocessor = Preprocessor(settings, mask_img)

    # Class to handle all analysis
    analyzer = Analyzer(settings, mask_img)


    ### Wait For Scan To Start -----------------------------
    while not scanReceiver.scanStarted: time.sleep(.5)
    logger.debug('Scan started')


    ### Process scan  -------------------------------------
    # Loop over all expected volumes
    for volIdx in range(settings['numTimepts']):

        # make sure this volume has arrived before continuing
        while not scanReceiver.completedVols[volIdx]: time.sleep(.1)

        ### Retrieve the raw volume, and preprocess. Preprocessing
        # will occur according to the parameters specified in 'settings'
        rawVol = scanReceiver.get_vol(volIdx)
        preprocVol = preprocessor.runPreprocessing(rawVol, volIdx)

        ### Analyze this volume
        result = analyzer.runAnalysis(preprocVol, volIdx)
        results.append(result)

    # shutdown thread
    scanReceiver.stop()



### ----------------------------------------------
if __name__ == '__main__':
    launchPyneal()
