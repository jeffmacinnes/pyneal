"""
Set of utilities for real-time analysis with Pyneal. These tools will apply the
specified analysis steps to incoming volume data during a real-time scan
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
        if settings['maskBinarizeChoice'] == False:
            self.weightMask = True
            self.weights = mask_img.get_data().copy()
            self.mask = mask_img.get_data() > 0
        else:
            self.weightMask = False
            self.mask = mask_img.get_data() > 0

        ### Set the analysis function based on the settings
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
        self.logger.debug('analyzed vol: {}'.format(volIdx))
        return vol


    def averageFromMask(self, vol):
        pass


    def medianFromMask(self, vol):
        pass
