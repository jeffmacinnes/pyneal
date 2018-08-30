import os
from os.path import join
import sys

import helper_tools

# get dictionary with relevant paths for tests within this module
paths = helper_tools.get_pyneal_scanner_test_paths()
sys.path.insert(0, paths['pynealDir'])
sys.path.insert(0, paths['pynealScannerDir'])

import pyneal_scanner.simulation.scannerSimulators.Siemens_sim as Siemens_sim

def test_Siemens_sim():
    """ Test pyneal_scanner.simulation.Siemens_sim """

    # set input args for Siemens_sim
    inputDir = paths['Siemens_funcDir']
    seriesNum = 13
    newSeriesNum = 999
    TR = 0

    # launch Siemens_sim, but have to mock input to start the sim
    Siemens_sim.input = lambda s : ''
    Siemens_sim.Siemens_sim(inputDir, seriesNum, newSeriesNum, TR)

    # remove the new dir
    Siemens_sim.rmFiles(inputDir, newSeriesNum)
