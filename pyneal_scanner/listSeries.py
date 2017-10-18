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


if __name__ == '__main__':

    # retrieve the path to the directory that holds this script
    pynealScannerDir = os.path.dirname(os.path.abspath(__file__))

    # initialize the ScannerSetting class. This will take care of
    # reading the config file (if found), or creating one if necessary
    scannerConfig = ScannerSettings(pynealScannerDir)

    # get the scanner manufacturer
    scannerMake = scannerConfig.get_scannerMake()
    print('scanner make is {}'.format(scannerMake))

    scannerPort= scannerConfig.get_socketPort()
    print('Scanner Port is: {}'.format(scannerPort))

    scannerHost = scannerConfig.get_socketHost()
    print('scanner host is: {}'.format(scannerHost))
