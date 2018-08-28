import os
from os.path import join
import sys
import shutil
import threading
from queue import Queue
import subprocess
import time

import zmq
import pytest

import helper_tools

# get dictionary with relevant paths for tests within this module
paths = helper_tools.get_pyneal_scanner_test_paths()
sys.path.insert(0, paths['pynealDir'])
sys.path.insert(0, paths['pynealScannerDir'])

import pyneal_scanner.utils.Siemens_utils as Siemens_utils
import pyneal_scanner.utils.general_utils as general_utils

### Tests for classes/functions within the Siemens_utils.py module
class Test_Siemens_utils():
    def test_Siemens_DirStructure(self):
        # update config file to match local paths
        configFile = join(paths['Siemens_dir'], 'scannerConfig.yaml')
        helper_tools.replace_scannerConfig_baseDir(configFile, paths['Siemens_funcDir'])

        # create instace of ScannerSettings class from general_utils
        scannerSettings = general_utils.ScannerSettings(paths['Siemens_dir'])

        # create instance of Philips_DirStructure for testing
        scannerDirs = Siemens_utils.Siemens_DirStructure(scannerSettings)

        ## Run through the Siemens_DirStructure class methods
        scannerDirs.print_currentSeries()
        assert scannerDirs.getUniqueSeries() == set(['000013'])

        ## Test waitForNewSeries function by simulating new series data
        # threading.timer object to copy in new data after a few sec
        newSeriesNum = 999
        t = threading.Timer(1.0, fakeNewSiemensSeries, [newSeriesNum])
        t.start()

        scannerDirs.waitForNewSeries()

        # assuming that didn't crash, stop the timer object and remove new file
        t.cancel()
        removeFakeSiemensSeries(newSeriesNum)

        # remove local paths from the config file
        helper_tools.cleanConfigFile(configFile)

    def test_Siemens_BuildNifti(self):
        """ Note: this module is already tested as part of the test_getSeries.py
        suite of tests. This function here is just included for the sake of
        consistency in writing these test blocks to correspond to the original
        source files
        """
        pass

    def test_Siemens_monitorSessionDir_and_Siemens_processMosaic(self):
        """ test Siemens_utils.Siemens_monitorSessionDir & Siemens_utils.Siemens_processMosaic

        Since these two classes work hand-in-hand, we test both in the same func
        """
        # create queue to store incoming file names
        dicomQ = Queue()
        sessionDir = paths['Siemens_funcDir']
        print(sessionDir)
        seriesNum = 999

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
        msg = 'hello from Siemens test'
        pyneal_socket.send_string(msg)
        msgResponse = pyneal_socket.recv_string()

        # start in instance of Siemens_monitorSessionDir. Note: runs in bg thread
        scanWatcher = Siemens_utils.Siemens_monitorSessionDir(sessionDir, seriesNum, dicomQ)
        scanWatcher.start()

        # start instance of slice processor. Note: runs in bg thread
        mosaicProcessor = Siemens_utils.Siemens_processMosaic(dicomQ, pyneal_socket)
        mosaicProcessor.start()

        # simulate a scan by copying new data into the session dir
        fakeNewSiemensSeries(seriesNum, nVols=3)

        # assuming it didn't crash, cancel the bg thread and delete new dir
        scanWatcher.stop()
        mosaicProcessor.stop()
        recvSocket.stop()
        removeFakeSiemensSeries(seriesNum, nVols=3)


@pytest.mark.skip(reason="we want the test methods to call this, not pytest itself")
def fakeNewSiemensSeries(newSeriesNum, nVols=1):
    """ Unlike GE and Philips, Siemens stores new series in the same dir as
    other series, instead of a unqiue dir for every series. So, we'll just
    fake that by copying an existing Siemens dcm, renaming with a new
    series number, and saving in the same directory.

    Parameters
    ----------
    newSeriesNum : int
        series number to assign to new copied data
    nVols : int, optional
        number of volumes to copy. Defaults to 1 vol; max 3
    """
    assert nVols <= 3, "nVols must be less than or equal to 3"
    for imageNum, i in enumerate(range(nVols), 1):
        origFile = join(paths['Siemens_funcDir'], ('001_000013_' + str(imageNum).zfill(6) + '.dcm'))
        newFile = join(paths['Siemens_funcDir'], ('001_' + str(newSeriesNum).zfill(6) + '_' + str(imageNum).zfill(6) + '.dcm'))
        shutil.copyfile(origFile, newFile)

@pytest.mark.skip(reason="we want the test methods to call this, not pytest itself")
def removeFakeSiemensSeries(seriesNum, nVols=1):
    """ Remove the simulated new series from the test Siemens data dir """
    assert nVols <= 3, "nVols must be less than or equal to 3"
    for imageNum, i in enumerate(range(nVols), 1):
        fName = join(paths['Siemens_funcDir'], ('001_' + str(seriesNum).zfill(6) + '_' + str(imageNum).zfill(6) + '.dcm'))
        os.remove(fName)
