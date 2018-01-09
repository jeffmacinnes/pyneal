"""
Set of utilities for preprocessing for Pyneal. These tools will apply the
specified preprocessing steps to incoming volume data during a real-time scan
"""
# python 2/3 compatibility
from __future__ import print_function

import os
import sys
from os.path import join
import time
import logging

import yaml
import nibabel as nib



class Preprocessor:
    """
    Preprocessing class. The methods of this class can be used to
    set up and execute preprocessing steps on incoming volumes during
    a real-time scan
    """
    def __init__(self, settings, mask_img):
        """
        settings: user settings dictionary
        mask_img: Nibabel image of the mask specified in the settings file
        """
        # set up logger
        self.logger = logging.getLogger('PynealLog')

        self.mask = mask_img
        self.settings = settings


    def runPreprocessing(self, vol, volIdx):
        """
        Run preprocessing on the supplied volume
        """
        self.logger.debug('preprocessed vol: {}'.format(volIdx))
        return vol
