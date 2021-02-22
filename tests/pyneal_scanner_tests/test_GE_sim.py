import os
from os.path import join
import sys
import mock

import pynealScanner_helper_tools as helper_tools


# get dictionary with relevant paths for tests within this module
paths = helper_tools.get_pyneal_scanner_test_paths()
for path in [paths['pynealDir'], paths['pynealScannerDir']]:
    if path not in sys.path:
        sys.path.insert(0, path)
import pyneal_scanner.simulation.scannerSimulators.GE_sim as GE_sim


def test_GE_sim():
    """ Test pyneal_scanner.simulation.GE_sim """

    # set input args for GE_sim
    dicomDir = join(paths['GE_funcDir'], 's1925')
    outputDir = join(paths['GE_funcDir'], 'sTEST')
    TR = 0

    # launch GE_sim, but have to mock input to start the sim
    GE_sim.input = lambda s : ''
    GE_sim.GE_sim(dicomDir, outputDir, TR)

    # remove the new dir
    GE_sim.rmOutputDir(outputDir)
