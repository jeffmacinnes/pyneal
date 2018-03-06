"""
Template for creating customized analyses in Pyneal. This tool allows users
to design and implement unique analysis routines for use during a real-time
fMRI scan

The custom analysis routines are contained in a single class (called, weirdly
enough, CustomAnalysis). There are 2 important components to this class: the
'__init__' method and the 'compute' method.

The '__init__' method should contain all of the code you want executed BEFORE the
start of the real-time run. This could include setting up any necessary paths,
or loading any additional files (e.g. libraries, ROIs, trained classifiers, etc).
In addition, the class also provides a reference to the mask_img that is specified
from the Pyneal Setup GUI. Users can choose to use this mask, or ignore completely.

The 'compute' method, on the other hand, should contain all of the code you want
executed on EACH NEW VOLUME as the scan is progression. The compute method, in
other words, is what actually gets called and executed during the scan. The only
stipulation is that the output gets returned as a dictionary called 'result' at
the end of each compute call. The 'result' dictionary can contain as many
key:value pairs as needed. The entire dictionary will get passed along to the
results server, where it will be tagged with a key indicating which volIdx the
results pertain to.

The CustomAnalysis template below has some specific variables pre-set that will
ensure that the class can integrate into the rest of the Pyneal workflow. Please
make sure to contain all of your edits within the sections labeled
"USER-SPECIFIED CODE"
"""

import sys
import os
from os.path import join
import numpy as np


class CustomAnalysis:
    def __init__(self, mask_img):
        """
        Everything in the __init__ class will be executed BEFORE the scan begins
        """
        self.mask = mask_img        # local reference to MASK from Pyneal setup GUI

        # add the directory that this script lives in to the path. This way it
        # is easy to load any additional files you want to put in the same
        # directory as your custom analysis script
        self.customAnalysisDir = os.path.abspath(os.path.dirname(__file__))
        sys.path.append(self.customAnalysisDir)

        ########################################################################
        ############# vvv INSERT USER-SPECIFIED CODE BELOW vvv #################
        self.myResult = 1



        ############# ^^^ END USER-SPECIFIED CODE ^^^ ##########################
        ########################################################################



    def compute(self, volume):
        """
        Code that will be executed on EACH new 3D volume that arrives DURING the
        real-time scan. Results must be returned in a dictionary
        """
        ########################################################################
        ############# vvv INSERT USER-SPECIFIED CODE BELOW vvv #################
        self.myResult += 1




        ############# ^^^ END USER-SPECIFIED CODE ^^^ ##########################
        ########################################################################

        return {'result': self.myResult}
