""" Template for creating customized analyses in Pyneal.

This tool allows users to design and implement unique analysis routines for
use during a real-time fMRI scan

The custom analysis routines are contained in a single class (called
CustomAnalysis). There are 2 important components to this class: the
'__init__' method and the 'compute' method.

The '__init__' method should contain all of the code you want executed BEFORE
the start of the real-time run. This could include setting up any necessary
paths, or loading any additional files (e.g. libraries, ROIs, trained
classifiers, etc). In addition, the class also provides a reference to the
mask_img that is specified from the Pyneal Setup GUI. Users can choose to use
this mask, or ignore completely.

The 'compute' method, on the other hand, should contain all of the code you
want executed on EACH NEW VOLUME as the scan is progression. The compute
method, in other words, is what actually gets called and executed during the
scan. The only stipulation is that the output gets returned as a dictionary
called 'result' at the end of each compute call. The 'result' dictionary can
contain as many key:value pairs as needed. The entire dictionary will get
passed along to the results server, where it will be tagged with a key
indicating which volIdx the results pertain to.

The CustomAnalysis template below has some specific variables pre-set that will
ensure that the class can integrate into the rest of the Pyneal workflow.
Please make sure to contain all of your edits within the sections labeled
"USER-SPECIFIED CODE"

"""
import sys
import os
from os.path import join
import logging

import numpy as np
import nibabel as nib


class CustomAnalysis:
    """ Custom Analysis Module

    This class contains all of the methods needed for setting up and executing
    customized analyses in Pyneal during a real-time scan

    """
    def __init__(self, maskFile, weightMask, numTimepts):
        """ Initialize the class

        Everything in the `__init__` method will be executed BEFORE the scan
        begins. This is a place to run any necessary setup code.

        The `__init__` method provides a number of inputs from the setup GUI
        that can be used to help set up a customized analyses. You are free to
        use or ignore these inputs as needed.

        Parameters
        ----------
        maskFile : string
            full path to the mask file specified in the Pyneal setup GUI
        weightMask : boolean
            flag indicating whether the "weight mask?" option in setup GUI was
            checked.
        numTimepts : int
            number of timepts in the run, as specified in the setup GUI

        """
        # Load masks and weights, and create an within-class reference to
        # each for use in later methods.
        mask_img = nib.load(maskFile)
        if weightMask is True:
            self.weights = mask_img.get_data().copy()
        self.mask = mask_img.get_data() > 0  # 3D boolean array of mask voxels

        # within-class reference to numTimepts for use in later methods
        self.numTimepts = numTimepts

        # Add the directory that this script lives in to the path. This way it
        # is easy to load any additional files you want to put in the same
        # directory as your custom analysis script
        self.customAnalysisDir = os.path.abspath(os.path.dirname(__file__))
        sys.path.append(self.customAnalysisDir)

        # Import the logger. If desired, you can write log messages to the
        # Pyneal log file using:
        # self.logger.info('my log message') - log file and stdOut
        # self.logger.debug('my log message') - log file only
        self.logger = logging.getLogger('PynealLog')

        ########################################################################
        ############# vvv INSERT USER-SPECIFIED CODE BELOW vvv #################
        self.myResult = 1



        ############# ^^^ END USER-SPECIFIED CODE ^^^ ##########################
        ########################################################################

    def compute(self, volume, volIdx):
        """ Compute method

        This method will be executed on EACH new 3D volume that arrives
        DURING the real-time scan. Results must be returned in a dictionary. No
        restrictions on dict key names or values, but note that the volume
        index will get added automatically by Pyneal before the result gets
        placed on the results server, so no need to specify that here

        Parameters
        ----------
        volume : nibabel-like image
            nibabel-like image containing a 3D array of voxel data, a (4,4)
            affine matrix mapping the volume to RAS+ space, and image metadata
        volIdx : int
            0-based index indicating where, in time (4th dimension), the volume
            belongs

        Returns
        -------
        dict
            dictionary containing key:value pair(s) for the results for the
            current volume

        """
        ########################################################################
        ############# vvv INSERT USER-SPECIFIED CODE BELOW vvv #################
        self.myResult += 1




        ############# ^^^ END USER-SPECIFIED CODE ^^^ ##########################
        ########################################################################

        return {'result': self.myResult}
