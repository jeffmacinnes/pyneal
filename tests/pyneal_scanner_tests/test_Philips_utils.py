import os
from os.path import join
import sys
import shutil
import threading
from queue import Queue
import subprocess

import zmq

import helper_tools

# get dictionary with relevant paths for tests within this module
paths = helper_tools.get_pyneal_scanner_test_paths()
sys.path.insert(0, paths['pynealDir'])
sys.path.insert(0, paths['pynealScannerDir'])

import pyneal_scanner.utils.Philips_utils as Philips_utils
import pyneal_scanner.utils.general_utils as general_utils

### Tests for classes/functions within the Philips_utils.py module
class Test_Philips_utils():
    def test_Philips_DirStructure(self):
        """ test Philips_utils.Philips_DirStucture """
        # update config file to match local paths
        configFile = join(paths['Philips_dir'], 'scannerConfig.yaml')
        helper_tools.replace_scannerConfig_baseDir(configFile, paths['Philips_funcDir'])

        # create instace of ScannerSettings class from gneral_utils
        scannerSettings = general_utils.ScannerSettings(paths['Philips_dir'])

        # create instance of Philips_DirStructure for testing
        scannerDirs = Philips_utils.Philips_DirStructure(scannerSettings)

        ### Run through Philips_DirStructure class methods
        scannerDirs.print_currentSeries()
        assert scannerDirs.get_seriesDirs() == ['0001']

        ### Test the waitForSeriesDir function by creating a fake dir
        # threading.timer object to create a new dir after a few sec
        fakeNewSeries = join(paths['Philips_funcDir'], '0TEST')
        t = threading.Timer(1.0, helper_tools.createFakeSeriesDir(fakeNewSeries))
        t.start()

        scannerDirs.waitForSeriesDir()

        # assuming it didn't crash, cancel the timer function and delete new dir
        t.cancel()
        shutil.rmtree(fakeNewSeries)

        # remove local paths from the config file
        helper_tools.cleanConfigFile(configFile)
