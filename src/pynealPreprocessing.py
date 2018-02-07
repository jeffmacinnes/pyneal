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
from threading import Thread
from queue import Queue

import yaml
import numpy as np
import nibabel as nib
from nipy.algorithms.registration import HistogramRegistration, Rigid



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
        self.affine = None

        # start the motion thread
        self.motionProcessor = MotionProcessor(logger=self.logger)
        # self.motionProcessor.daemon = True
        # self.motionProcessor.start()
        # self.logger.debug('Starting motion processor')


    def set_affine(self, affine):
        """
        make a local reference to the RAS+ affine transformation for this series
        """
        self.affine = affine


    def runPreprocessing(self, vol, volIdx):
        """
        Run preprocessing on the supplied volume
        """
        ### calculate the motion parameters on this volume
        # NOTE: estimateMotion needs the input vol to be a nibabel nifti obj
        self.motionProcessor.estimateMotion(nib.Nifti1Image(vol, self.affine),
                                            volIdx)

        self.logger.debug('preprocessed vol: {}'.format(volIdx))
        return vol


class MotionProcessor():
    """
    Tool to estimate 6-deg of rigid-body motion. The motion estimates will be
    made relative to the first volume in the series.

    Motion estimation algorithm based on:
    https://github.com/cni/rtfmri/blob/master/rtfmri/analyzers.py
    """
    def __init__(self, logger=None, interval=.1):
        # start the thread upon creation
        #Thread.__init__(self)

        #self.motionQ = motionQ
        self.logger = logger
        self.interval = interval

        self.refVol = None

        # create a starting motion estimate
        self.previousEstimate = Rigid(np.eye(4))


    def estimateMotion(self, niiVol, volIdx):
        if volIdx < 2:
            print('Vol {} - no motion calculated'.format(volIdx))
        elif volIdx == 2:
            self.refVol = niiVol
            print('Vol {} - reference volume set'.format(volIdx))
        elif volIdx > 2:
            start = time.time()
            print('calculating motion on vol {}'.format(volIdx))
            reg = HistogramRegistration(niiVol, self.refVol, interp='tri')
            T = reg.optimize(self.previousEstimate, optimizer='powell', ftol=0.1, maxfun=10)
            print('Translations: {}'.format(T.translation))
            print('Rotations: {}'.format(T.rotation))
            print('took: {}'.format(time.time()-start))

            # update the estimate
            self.previousEstimate = T
