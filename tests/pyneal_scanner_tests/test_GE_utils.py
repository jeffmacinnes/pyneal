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

import pyneal_scanner.utils.GE_utils as GE_utils
import pyneal_scanner.utils.general_utils as general_utils


### Tests for classses/functions within the GE_utils.py module.
class Test_GE_utils():
    def test_GE_DirStructure(self):
        """ test GE_utils.GE_DirStructure """

        # update config file to match local paths
        configFile = join(paths['GE_dir'], 'scannerConfig.yaml')
        helper_tools.replace_scannerConfig_baseDir(configFile, paths['GE_funcDir'])

        # create instance of ScannerSettings class from general_utils
        scannerSettings = general_utils.ScannerSettings(paths['GE_dir'])

        # create instance of GE_DirStructure for testing
        scannerDirs = GE_utils.GE_DirStructure(scannerSettings)

        ### Run through the GE_DirStructure class methods
        scannerDirs.print_currentSeries()

        # confirm paths match test directories
        assert scannerDirs.get_seriesDirs() == ['s1925']
        assert scannerDirs.get_pDir() == 'p1'
        assert scannerDirs.get_eDir() == 'e123'
        assert scannerDirs.get_sessionDir() == join(paths['GE_dir'], 'p1/e123')

        ### Test the waitForSeriesDir function by creating a fake dir
        # threading.timer object to create a new directory after a few sec
        fakeNewSeries = join(paths['GE_funcDir'], 'p1/e123/sTEST')
        t = threading.Timer(1.0, helper_tools.createFakeSeriesDir(fakeNewSeries))
        t.start()

        scannerDirs.waitForSeriesDir()

        # assuming it didn't crash, cancel the timer function and delete new dir
        t.cancel()
        shutil.rmtree(fakeNewSeries)

        # remove local paths from config file
        helper_tools.cleanConfigFile(configFile)

    def test_GE_BuildNifti(self):
        """ Note: this module is already tested as part of the test_getSeries.py
        suite of tests. This function here is just included for the sake of
        consistency in writing these test blocks to correspond to the original
        source files
        """
        pass

    def test_GE_monitorSeriesDir_and_GE_processSlice(self):
        """ test GE_utils.GE_monitorSeriesDir & GE_utils.GE_processSlice

        Since these two classes work hand-in-hand, we test both in the same func
        """
        # create queue to store incoming file names
        dicomQ = Queue()
        newSeriesDir = join(paths['GE_funcDir'], 'p1/e123/sTEST')
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
        msg = 'hello from GE test'
        pyneal_socket.send_string(msg)
        msgResponse = pyneal_socket.recv_string()

        # start in instance of GE_monitorSeriesDir. Note: runs in bg thread
        scanWatcher = GE_utils.GE_monitorSeriesDir(newSeriesDir, dicomQ)
        scanWatcher.start()

        # start instance of slice processor. Note: runs in bg thread
        sliceProcessor = GE_utils.GE_processSlice(dicomQ, pyneal_socket)

        # copy contents of existing GE test data dir to new dir, simulating scan
        GE_seriesDir = join(paths['GE_funcDir'], 'p1/e123/s1925')
        helper_tools.copyScanData(GE_seriesDir, newSeriesDir)

        # assuming it didn't crash, cancel the bg thread and delete new dir
        scanWatcher.stop()
        sliceProcessor.stop()
        recvSocket.stop()
        shutil.rmtree(newSeriesDir)
