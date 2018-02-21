"""
Set of utilities for real-time analysis with Pyneal. These tools will apply the
specified analysis steps to incoming volume data during a real-time scan

Note: The output from every analysis function needs to be a dictionary that stores
the results for that volume. As long as that criterion is met, all key names and
formatting are completely up to the particular analysis function
"""
# python 2/3 compatibility
from __future__ import print_function

import os
import sys
from os.path import join
import time
import logging

import yaml
import numpy as np
import nibabel as nib


class Analyzer:
    """
    Analysis class. The methods of this class can be used to
    run the specified analysis on each volume during a real-time scan
    """
    def __init__(self, settings, mask_img):
        """
        settings: user settings dictionary
        mask_img: Nibabel image of the mask specified in the settings file
        """
        # set up logger
        self.logger = logging.getLogger('PynealLog')

        # create reference to settings dict
        self.settings = settings

        ### Format the mask. If the settings specify that the the mask should
        # be weighted, create separate vars for the weights and mask
        if settings['maskIsWeighted'] == True:
            self.weightMask = True
            self.weights = mask_img.get_data().copy()
            self.mask = mask_img.get_data() > 0
        else:
            self.weightMask = False
            self.mask = mask_img.get_data() > 0

        ### Set the appropriate analysis function based on the settings
        if settings['analysisChoice'] == 'Average':
            self.analysisFunc = self.averageFromMask
        elif settings['analysisChoice'] == 'Median':
            self.analysisFunc = self.medianFromMask
        else:
            print('No function specified for {} option yet!'.format(settings['analysisChoice']))


    def runAnalysis(self, vol, volIdx):
        """
        Run preprocessing on the supplied volume
        """
        output = self.analysisFunc(vol)
        self.logger.debug('analyzed vol: {}'.format(volIdx))
        return output


    def averageFromMask(self, vol):
        """
        Compute the average voxel activation within the mask.
        Note: np.average has weights option, np.mean doesn't

        outputs: {'weightedAverage': ####} or {'average': ####}
        """
        if self.weightMask:
            result = np.average(vol[self.mask], weights=self.weights[self.mask])
            return {'weightedAverage': np.round(result, decimals=2)}
        else:
            result = np.mean(vol[self.mask])
            return {'average': np.round(result, decimals=2)}


    def medianFromMask(self, vol):
        """
        Compute the median voxel activation within the mask
        Note: weighted median algorithm from: https://pypi.python.org/pypi/weightedstats/0.2

        outputs: {'weightedMedian': ####} or {'median': ####}
        """
        if self.weightMask:
            data = vol[self.mask]
            sorted_data, sorted_weights = map(np.array, zip(*sorted(zip(data, self.weights[self.mask]))))
            midpoint = 0.5 * sum(sorted_weights)
            if any(self.weights[self.mask] > midpoint):
                return (data[weights == np.max(weights)])[0]
            cumulative_weight = np.cumsum(sorted_weights)
            below_midpoint_index = np.where(cumulative_weight <= midpoint)[0][-1]
            if cumulative_weight[below_midpoint_index] == midpoint:
                return np.mean(sorted_data[below_midpoint_index:below_midpoint_index+2])
            result = sorted_data[below_midpoint_index+1]
            return {'weightedMedian': np.round(result, decimals=2)}
        else:
            # take the median of the voxels in the mask
            result = np.median(vol[self.mask])
            return {'median': np.round(result, decimals=2)}
