import os
from os.path import join
import sys
import mock

import helper_tools

# get dictionary with relevant paths for tests within this module
paths = helper_tools.get_pyneal_scanner_test_paths()
sys.path.insert(0, paths['pynealDir'])
sys.path.insert(0, paths['pynealScannerDir'])

import pyneal_scanner.simulation.scannerSimulators.Philips_sim as Philips_sim

def test_Philips_sim():
    """ Test pyneal_scanner.simulation.Philips_sim """

    # set input args for Philips_sim
    inputDir = join(paths['Philips_funcDir'], '0001')
    outputDir = join(paths['Philips_funcDir'], '0TEST')
    TR = 0

    # launch Philips_sim, but have to mock input to start the sim
    Philips_sim.input = lambda s : ''
    Philips_sim.Philips_sim(inputDir, outputDir, TR)

    # remove the new dir
    Philips_sim.rmOutputDir(outputDir)
