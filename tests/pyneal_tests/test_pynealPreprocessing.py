import os
from os.path import join
import sys

import numpy as np
import nibabel as nib

import pyneal_helper_tools as helper_tools

# get dictionary with relevant paths for tests within this module
paths = helper_tools.get_pyneal_test_paths()
if paths['pynealDir'] not in sys.path:
        sys.path.insert(0, paths['pynealDir'])

from src.pynealPreprocessing import Preprocessor
from src.pynealPreprocessing import MotionProcessor

# inputs to preprocessor
seriesFile = join(paths['testDataDir'], 'testSeries.nii.gz')
settings = {'launchDashboard': False, 'estimateMotion': True}

class Test_pynealPreprocessing:
    """ Test pyneal.src.pynealPreprocessing module """

    def test_runPreprocessing(self):
        # create instance of Preprocessor class
        preprocessor = Preprocessor(settings)

        # loop over series and test preprocessing on each volume
        seriesData = nib.load(seriesFile)
        results = []
        for volIdx in range(seriesData.shape[3]):
            # extract the 3d array for this vol
            thisVol = seriesData.get_data()[:, :, :, volIdx]
            preprocVol = preprocessor.runPreprocessing(thisVol, volIdx)


    def test_estimateMotion(self):
        # create instance of Motion Processor class
        motionProcessor = MotionProcessor(refVolIdx=0)

        # loop over series and test preprocessing on each volume
        seriesData = nib.load(seriesFile)
        rms_abs_results = []
        rms_rel_results = []
        for volIdx in range(seriesData.shape[3]):
            # extract the 3d array for this vol and convert to niftiobject
            thisVol = seriesData.get_data()[:, :, :, volIdx]
            thisVol_nii = nib.Nifti1Image(thisVol, np.eye(4))

            motionParams = motionProcessor.estimateMotion(thisVol_nii, volIdx)

            if motionParams is not None:
                rms_abs_results.append(motionParams['rms_abs'])
                rms_rel_results.append(motionParams['rms_rel'])

        # compare computed results to expected results
        rms_abs_results = np.array(rms_abs_results)
        expected_abs_results = np.array([0.002865, 0.003250])
        np.testing.assert_almost_equal(rms_abs_results, expected_abs_results, decimal=6)

        rms_rel_results = np.array(rms_rel_results)
        expected_rel_results = np.array([0.002865, 0.0024558])
        np.testing.assert_almost_equal(rms_rel_results, expected_rel_results, decimal=6)
