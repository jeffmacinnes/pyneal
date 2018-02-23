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
import zmq
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
        self.motionProcessor = MotionProcessor(logger=self.logger, refVolIdx=4)

        # create the socket to send data to dashboard (if dashboard there be)
        if self.settings['launchDashboard']:
            self.dashboard = True
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
        ### calculate the motion parameters on this volume. motionParams are
        # returned as dictionary with keys for 'rms_abs', and 'rms_rel';
        # NOTE: estimateMotion needs the input vol to be a nibabel nifti obj
        # the nostdout bit suppresses verbose estimation output to stdOut
        with nostdout():
            motionParams = self.motionProcessor.estimateMotion(
                                nib.Nifti1Image(vol,self.affine),
                                volIdx)

        ### send to dashboard (if specified)
        if self.settings['launchDashboard']:
            if motionParams is not None:

                # send to the dashboard
                self.sendToDashboard(topic='motion',
                                    content={'volIdx':volIdx,
                                            'rms_abs': motionParams['rms_abs'],
                                            'rms_rel': motionParams['rms_rel']})

        self.logger.debug('preprocessed vol: {}'.format(volIdx))
        return vol


    def sendToDashboard(self, topic=None, content=None):
        """
        If dashboard is launched, send the msg to the dashboard. The dashboard
        expects messages formatted in specific way, namely a dictionary with 2
        keys: 'topic', and 'content'

        Any message from the scanReceiver should set the topic as
        'pynealScannerLog', and the content should be it's own dictionary with
        the key 'logString'. logString should contain the log message you want
        the dashboard to display
        """
        if self.dashboard:
            dashboardMsg = {'topic': topic,
                            'content': content}
            self.dashboardSocket.send_json(dashboardMsg)
            response = self.dashboardSocket.recv_string()


class MotionProcessor():
    """
    Tool to estimate motion. The motion estimates will be made relative to
    a reference volume, specifed by refVolIdx (0-based index).

    Motion estimation based on:
    https://github.com/cni/rtfmri/blob/master/rtfmri/analyzers.py &
    https://www.sciencedirect.com/science/article/pii/S1053811917306729#bib32
    """
    def __init__(self, logger=None, refVolIdx=4):
        self.logger = logger
        self.refVolIdx = refVolIdx
        self.refVol = None

        # initialize
        self.refVol_T = Rigid(np.eye(4))
        self.prevVol_T = Rigid(np.eye(4))


    def estimateMotion(self, niiVol, volIdx):
        """
        Estimate the motion parameters for the current volume. This tool will
        first estimate the transformation needed to align the current volume to
        the reference volume. This transformation can be expressed as a rigid
        body transformation with 6 degrees of freedom (translation x,y,z;
        rotation x,y,z).

        Using the estimated transformation matrix, we can compute RMS deviation
        as a single value representing the displacement (in mm) between the
        current volume and the reference volume (abs rms) or the current volume
        and the previous volume (relative rms).

        This approach for estimating motion borrows heavily from:
        https://github.com/cni/rtfmri/blob/master/rtfmri/analyzers.py

        RMS calculations:
        https://www.fmrib.ox.ac.uk/datasets/techrep/tr99mj1/tr99mj1.pdf

        Inputs:
            niiVol: nibabel-like 3D data object, representing the current volume
            volIdx: the index of the current volume along the 4th dim (i.e. time)
        """
        if volIdx < self.refVolIdx:
            return None

        elif volIdx == self.refVolIdx:
            self.refVol = niiVol            # set the reference volume
            return None

        elif volIdx > self.refVolIdx:
            # create a regisitration object
            reg = HistogramRegistration(niiVol, self.refVol, interp='tri')

            # estimate optimal transformation
            T = reg.optimize(self.prevVol_T.copy(), ftol=0.1, maxfun=30)

            # compute RMS relative to reference vol (rms abs)
            rms_abs = self.computeRMS(self.refVol_T, T)

            # compute RMS relative to previous vol (rms rel)
            rms_rel = self.computeRMS(self.prevVol_T, T)

            # # get the realignment parameters:
            # rot_x, rot_y, rot_z = np.rad2deg(T.rotation)
            # trans_x, trans_y, trans_z = T.translation

            # update the estimate
            self.prevVol_T = T

            motionParams = {'rms_abs': rms_abs,
                            'rms_rel': rms_rel}
            return motionParams


    def computeRMS(self, T1, T2, R=50):
        """
        Compute the RMS displacement between transformation matrices. Returns
        a single value reprsenting the mean displacement in mm (assuming a
        spherical volume with radius, R).

        R defaults to 50mm (apprx distance from cerebral cortex to center of head):
            Motion-related artifacts in structural brain images revealed with
            independent estimates of in-scanner head motion. (2017) Savalia, et al.
            Human Brain Mapping. Jan; 38(1)
            https://www.ncbi.nlm.nih.gov/pubmed/27634551

        This approach for estimating motion borrows heavily from:
        https://github.com/cni/rtfmri/blob/master/rtfmri/analyzers.py

        RMS calculations:
        https://www.fmrib.ox.ac.uk/datasets/techrep/tr99mj1/tr99mj1.pdf
        """
        diffMatrix = T1.as_affine().dot(np.linalg.inv(T2.as_affine())) - np.eye(4)

        # decompose into A and t components
        A = diffMatrix[:3, :3]
        t = diffMatrix[:3, 3]

        # volume center assumed to be at 0,0,0 in world space coords
        center = np.zeros(3)
        t += A.dot(center)

        # compute RMS error (aka deviation error between transforms)
        rms = np.sqrt((1/5) * R**2 * A.T.dot(A).trace() + t.T.dot(t))

        return rms


# suppress stdOut from verbose functions
@contextlib.contextmanager
def nostdout():
    save_stdout = sys.stdout
    sys.stdout = io.StringIO()
    yield
    sys.stdout = save_stdout
