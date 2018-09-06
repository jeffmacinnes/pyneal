import os
from os.path import join
import sys
import importlib

import numpy as np
import nibabel as nib

import pyneal_helper_tools as helper_tools

# get dictionary with relevant paths for tests within this module
paths = helper_tools.get_pyneal_test_paths()
if paths['pynealDir'] not in sys.path:
        sys.path.insert(0, paths['pynealDir'])

# import the pynealScanner_sim module
spec = importlib.util.spec_from_file_location("pynealScanner_sim",
            join(paths['pynealDir'], 'utils/simulation/pynealScanner_sim.py'))
pynealScanner_sim = importlib.util.module_from_spec(spec)
spec.loader.exec_module(pynealScanner_sim)


class Test_pynealScanner_sim():
    """ tests for utils.simulation.pynealScanner_sim """

    def test_prepRealDataset(self):
        """ test pynealScanner_sim.prepRealDataset """
        testDataset = join(paths['testDataDir'], 'testSeries.nii.gz')
        ds = pynealScanner_sim.prepRealDataset(testDataset)

        # load the same dataset manually for comparison
        ds_cmp = nib.load(testDataset)

        # confirm that the shape of returned ds matches input file
        assert ds.shape == ds_cmp.shape
        assert type(ds) == type(ds_cmp)

    def test_prepRandomDataset(self):
        """ test pynealScanner_sim.prepRandomDataset """
        dims = [64, 64, 20, 5]
        ds = pynealScanner_sim.prepRandomDataset(dims)

        # confirm that the shape of returned ds
        assert ds.shape == tuple(dims)

    def test_pynealScannerSimulator(self):
        """ test pynealScanner_sim.pynealScannerSimulator """
        port = 5555

        # load test dataset
        ds = nib.load(join(paths['testDataDir'], 'testSeries.nii.gz'))
        nVols = ds.shape[3]

        # launch a simulated version of pyneal receiving socket
        simRecvSocket = helper_tools.SimRecvSocket('127.0.0.1',
                                                    port,
                                                    nVols)
        simRecvSocket.daemon = True
        simRecvSocket.start()

        # run pynealScannerSimulator
        pynealScanner_sim.input = lambda s : ''     # mock the input to start scan
        pynealScanner_sim.pynealScannerSimulator(ds, TR=0, port=port)

        # assuming nothing crashed, shut down simRecvSocket
        simRecvSocket.stop()
