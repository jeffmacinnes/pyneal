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
import io
import contextlib

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

        # create the socket to send data to dashboard (if specified)
        if self.settings['launchDashboard']:
            context = zmq.Context.instance()
            self.dashboardSocket = context.socket(zmq.REQ)
            self.dashboardSocket.connect('tcp://127.0.0.1:{}'.format(self.settings['dashboardPort']))


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
        with nostdout():
            motionParams = self.motionProcessor.estimateMotion(
                                nib.Nifti1Image(vol,self.affine),
                                volIdx
                                )

        print(motionParams)
        self.logger.debug('preprocessed vol: {}'.format(volIdx))
        return vol


class MotionProcessor():
    """
    Tool to estimate 6-deg of rigid-body motion. The motion estimates will be
    made relative to the first volume in the series.

    Motion estimation algorithm based on:
    https://github.com/cni/rtfmri/blob/master/rtfmri/analyzers.py
    """
    def __init__(self, logger=None, skipVols=4):
        # start the thread upon creation
        #Thread.__init__(self)

        #self.motionQ = motionQ
        self.logger = logger
        self.skipVols = skipVols

        self.refVol = None

        # create a starting motion estimate
        self.previousEstimate = Rigid(np.eye(4))


    def estimateMotion(self, niiVol, volIdx):
        if volIdx < self.skipVols:
            motionParams = {'translation':np.zeros(3),
                            'rotation': np.zeros(3)}
        elif volIdx == self.skipVols:
            self.refVol = niiVol
            motionParams = {'translation':np.zeros(3),
                            'rotation': np.zeros(3)}
        elif volIdx > self.skipVols:
            reg = HistogramRegistration(niiVol, self.refVol, interp='tri')
            T = reg.optimize(self.previousEstimate, ftol=0.1, maxfun=30)

            motionParams = {'translation':T.translation,
                            'rotation': T.rotation}

            # update the estimate
            self.previousEstimate = T

        return motionParams

# suppress stdOut from verbose functions
@contextlib.contextmanager
def nostdout():
    save_stdout = sys.stdout
    sys.stdout = io.StringIO()
    yield
    sys.stdout = save_stdout
