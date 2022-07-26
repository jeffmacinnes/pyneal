import os
from os.path import join
import sys
import shutil
import threading
from queue import Queue
import subprocess

import zmq

import pynealScanner_helper_tools as helper_tools

# get dictionary with relevant paths for tests within this module
paths = helper_tools.get_pyneal_scanner_test_paths()
for path in [paths['pynealDir'], paths['pynealScannerDir']]:
    if path not in sys.path:
        sys.path.insert(0, path)

import pyneal_scanner.utils.Philips_utils as Philips_utils
import pyneal_scanner.utils.general_utils as general_utils

### Tests for classes/functions within the Philips_utils.py module
class Test_Philips_utils():
    def test_Philips_DirStructure(self):
        """ test Philips_utils.Philips_DirStucture """
        # update config file to match local paths
        configFile = join(paths['Philips_dir'], 'scannerConfig.yaml')
        helper_tools.replace_scannerConfig_sessionDir(configFile, paths['Philips_funcDir'])

        # create instance of ScannerSettings class from general_utils
        scannerSettings = general_utils.ScannerSettings(paths['Philips_dir'])

        # create instance of Philips_DirStructure for testing
        scannerDirs = Philips_utils.Philips_DirStructure(scannerSettings)

        ### Run through Philips_DirStructure class methods
        scannerDirs.print_currentSeries()
        assert scannerDirs.get_seriesDirs() == ['0001','0TEST']

        ### Test the waitForSeriesDir function by creating a fake dir
        # threading.timer object to create a new dir after a few sec
        fakeNewSeries = join(paths['Philips_funcDir'], '0TEST')
        t = threading.Timer(1.0, helper_tools.createFakeSeriesDir, [fakeNewSeries])
        t.start()

        scannerDirs.waitForSeriesDir()

        # assuming it didn't crash, cancel the timer function and delete new dir
        t.cancel()
        shutil.rmtree(fakeNewSeries)

        # remove local paths from the config file
        helper_tools.cleanConfigFile(configFile)

    def test_Philips_BuildNifti(self):
        """ Note: this module is already tested as part of the test_getSeries.py
        suite of tests. This function here is just included for the sake of
        consistency in writing these test blocks to correspond to the original
        source files
        """
        pass

    def test_Philips_monitorSeriesDir_and_Philips_processVolume(self):
        """ test Philips_utils.Philips_monitorSeriesDir & Philipt_utils.Philips_processVolume

        Since these two classes work hand in hand, we test both in the same function
        """
        # create queue to store incoming par files
        parQ = Queue()
        newSeriesDir = join(paths['Philips_funcDir'], '0TEST')
        helper_tools.createFakeSeriesDir(newSeriesDir)

        ## Set up sockets to send data between
        host = '127.0.0.1'
        port = 5555
        nVols = 3

        # create a scanner side socket to talk to simulated pyneal socket
        pyneal_socket = general_utils.create_pynealSocket(host, port)

        # start simulated pyneal-side socket to receive data
        recvSocket = helper_tools.SimRecvSocket(host, port, nVols)
        recvSocket.daemon = True
        recvSocket.start()

        # connect to simulated pyneal socket
        msg = 'hello from Philips test'
        pyneal_socket.send_string(msg)
        msgResponse = pyneal_socket.recv_string()

        # start in intance of Philips_monitorSeriesDir
        scanWatcher = Philips_utils.Philips_monitorSeriesDir(newSeriesDir, parQ)
        scanWatcher.start()

        # start an instance of Philips volume processor
        volProcessor = Philips_utils.Philips_processVolume(parQ, pyneal_socket)

        # copy contents of existing Philips test data dir to new dir, simulating scan
        Philips_seriesDir = join(paths['Philips_funcDir'], '0001')
        helper_tools.copyScanData(Philips_seriesDir, newSeriesDir)

        # assuming it didn't crash, cancel the bg threads and delete new dir
        scanWatcher.stop()
        volProcessor.stop()
        recvSocket.stop()
        shutil.rmtree(newSeriesDir)
