import os
from os.path import join
import sys
import socket
import json

import numpy as np

import helper_tools

# get dictionary with relevant paths for tests within this module
paths = helper_tools.get_pyneal_scanner_test_paths()
sys.path.insert(0, paths['pynealDir'])
pynealScannerPort = 5555

from src.scanReceiver import ScanReceiver

# Tests for functions within the resultsServer module
def test_resultsServer():
    """ tests pyneal.src.resultsServer """

    # create settings dictionary
    settings = {'pynealScannerPort': pynealScannerPort,
                'numTimepts': 3,
                'launchDashboard': False}
    scanReceiver = ScanReceiver(settings)
    scanReceiver.daemon = True
    scanReceiver.start()

    
