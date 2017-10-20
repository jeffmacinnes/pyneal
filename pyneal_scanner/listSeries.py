"""
List all of the series that are associated with the current session.

Show the name, timestamp, and filesize of each series as a way of helping to
link the series names with phases of your task (e.g. anat scan, task scans)
"""
from __future__ import print_function

import os
import sys
from os.path import join

from utils.general_utils import ScannerSettings

def listSeries():
    # Path to this directory
    pynealScannerDir = os.path.dirname(os.path.abspath(__file__))

    # Initialize the ScannerSetting class. This will take care of
    # reading the config file (if found), or creating one if necessary
    scannerConfig = ScannerSettings(pynealScannerDir)

    # Retrieve a dictionary of all settings in the config file
    scannerSettings = scannerConfig.get_all_settings()

    # Get the scanner make from the dictionary, and
    # if its not there, prompt user for it
    if 'scannerMake' in scannerSettings:
        scannerMake = scannerSettings['scannerMake']
    else:
        scannerMake = scannerConfig.get_scannerMake()
    print('='*15)
    print('Scanning Environment: {}'.format(scannerMake))

    # Import the appropriate tools for this scanning environment.
    # Regardless of the environment, give the tools the same name
    # so subsequent steps can proceed
    if scannerMake == 'GE':
        #######################################
        ### ---- GE RELEVANT COMMANDS ----- ###
        #######################################
        from utils.GE_utils import GE_DirStructure as ScannerDirs

        # check to see if a base directory is specified already
        if 'scannerBaseDir' in scannerSettings:
            scannerDirs = ScannerDirs(baseDir=scannerSettings['scannerBaseDir'])
        else:
            scannerDirs = ScannerDirs()

        # List all of the current series
        scannerDirs.listSeriesDirs()


    elif scannerMake == 'Phillips':
        #############################################
        ### ---- Phillips RELEVANT COMMANDS ----- ###
        #############################################
        pass

    elif scannerMake == 'Siemens':
        ############################################
        ### ---- Siemens RELEVANT COMMANDS ----- ###
        ############################################
        pass

    else:
        print('Unrecognized Scanner Make: {}'.format(scannerMake))



# If called directly from the command line
if __name__ == '__main__':
    listSeries()
