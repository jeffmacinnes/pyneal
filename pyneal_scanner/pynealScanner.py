"""
(Pyneal-Scanner: Command line function)
Call this tool to begin listening for new incoming series data during a
real-time run. This tool will read the scannerConfig file in an attempt to
determine the appropriate scanning environment and set the subsequent
processing tools appropriately.

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
debugging potential issues than what you see printed back to the terminal
window
"""

from __future__ import print_function

import os
import sys

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
    from utils.GE_utils import GE_launch_rtfMRI

    # launch a real-time session
    GE_launch_rtfMRI(scannerSettings, scannerDirs)


def pynealScanner_Phillips(scannerSettings, scannerDirs):
    """
    Tools for processing a real-time scan in a Phillips environment
    """
    from utils.Philips_utils import Philips_launch_rtfMRI

    # launch a real-time session
    Philips_launch_rtfMRI(scannerSettings, scannerDirs)


def pynealScanner_Siemens(scannerSettings, scannerDirs):
    """
    Tools for processing a real-time scan in a Siemens environment
    """
    from utils.Siemens_utils import Siemens_launch_rtfMRI

    # launch a real-time session
    Siemens_launch_rtfMRI(scannerSettings, scannerDirs)


def pynealScanner_sandbox(scannerSettings, scannerDirs):
    """
    method for launching a real-time scan using experimental methods.
    Mainly for debugging and testing
    """
    from sandbox.test_GE_utils import test_GE_launch_rtfMRI

    # launch a real-time session
    test_GE_launch_rtfMRI(scannerSettings, scannerDirs)


if __name__ == "__main__":

    ### set up logging
    # logging to file
    fileLogger = logging.FileHandler('./pynealScanner.log', mode='w')
    fileLogger.setLevel(logging.DEBUG)
    fileLogFormat = logging.Formatter('%(asctime)s - %(levelname)s - %(threadName)s - %(module)s, line: %(lineno)d - %(message)s',
                                      '%m-%d %H:%M:%S')
    fileLogger.setFormatter(fileLogFormat)

    # logging to console
    consoleLogger = logging.StreamHandler(sys.stdout)
    consoleLogger.setLevel(logging.INFO)
    consoleLogFormat = logging.Formatter('%(threadName)s -  %(message)s')
    consoleLogger.setFormatter(consoleLogFormat)

    # root logger, add handlers. (subsequent modules can access this same
    # logger by calling: logger = logging.getLogger(__name__)
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)
    logger.addHandler(fileLogger)
    logger.addHandler(consoleLogger)

    # initialize the session classes:
    scannerSettings, scannerDirs = initializeSession()

    # print all of the current settings and series dirs to the terminal
    scannerSettings.print_allSettings()
    scannerDirs.print_currentSeries()

    # load the appropriate tools for this scanning environment
    scannerMake = scannerSettings.allSettings['scannerMake']
    if scannerMake == 'GE':
        pynealScanner_GE(scannerSettings, scannerDirs)
    elif scannerMake == 'Philips':
        pynealScanner_Phillips(scannerSettings, scannerDirs)
    elif scannerMake == 'Siemens':
        pynealScanner_Siemens(scannerSettings, scannerDirs)
    elif scannerMake == 'sandbox':
        pynealScanner_sandbox(scannerSettings, scannerDirs)
    else:
        print('Unrecognized scanner make: {}'.format(scannerMake))
