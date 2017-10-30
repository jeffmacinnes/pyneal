"""
(Pyneal-Scanner: Command line function)
Call this tool to begin listening for new incoming series data during a
real-time run. This tool will read the scannerConfig file in an attempt to
determine the appropriate scanning environment and set the subsequent processing
tools appropriately.

This function has 3 overall goals:
    - monitor a sessionDir for NEW, incoming series data
    - read incoming data, and reformat to the standard format that pyneal is
    expecting (i.e. single slice data, oriented in RAS+)
    - send reformatted data to Pyneal via a socket connection

How these steps are implemented will vary according to the different scanning
environments.

Each time this function is called, a log file is written (or overwritten)
in the pyneal_scanner dir. This file will have verbose information about
everything that happens while this tool is running, and may be more useful in
debugging potential issues than what you see printed back to the terminal window
"""

from __future__ import print_function

import os
import sys
from os.path import join

import logging

from utils.general_utils import initializeSession

# Get the full path to where the pyneal_scanner directory is. This assumes
# getSeries.py was called directly from the command line (currently
# the only option)
pynealScannerDir = os.path.dirname(os.path.abspath(sys.argv[0]))


def pynealScanner_GE(scannerSettings, scannerDirs):
    """
    Tools for processing a real-time scan in a GE environment
    """
    #from utils.GE_utils import GE_rtfMRI

    logger.debug('You are in GE land, bub!')

def pynealScanner_Phillips(scannerSettings, scannerDirs):
    """
    Tools for processing a real-time scan in a Phillips environment
    """
    pass


def pynealScanner_Siemens(scannerSettings, scannerDirs):
    """
    Tools for processing a real-time scan in a Siemens environment
    """
    pass




if __name__ == "__main__":

    ### set up logging
    # write log messages to file if they are DEBUG level or higher
    logging.basicConfig(level=logging.DEBUG,
                        format='%(asctime)s - %(threadName)s - %(levelname)s - %(message)s',
                        datefmt='%m-%d %H:%M:%S',
                        filename='./pynealScanner.log',
                        filemode='w')

    # set up logging to console
    consoleLogger = logging.StreamHandler()
    consoleLogger.setLevel(logging.INFO)        # console will print logs if they are INFO or higher
    consoleLogFormat = logging.Formatter('%(threadName)s - %(levelname)-8s %(message)s')
    consoleLogger.setFormatter(consoleLogFormat)

    logging.getLogger(__name__).addHandler(consoleLogger)
    logger = logging.getLogger(__name__)

    # initialize the session classes:
    scannerSettings, scannerDirs = initializeSession()

    # load the appropriate tools for this scanning environment
    scannerMake = scannerSettings.allSettings['scannerMake']
    if scannerMake == 'GE':
        pynealScanner_GE(scannerSettings, scannerDirs)
    elif scannerMake == 'Phillips':
        pynealScanner_Phillips(scannerSettings, scannerDirs)
    elif scannerMake == 'Siemens':
        pynealScanner_Seimens(scannerSettings, scannerDirs)
    else:
        print('Unrecognized scanner make: {}'.format(scannerMake))
