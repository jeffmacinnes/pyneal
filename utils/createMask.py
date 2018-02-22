"""
Tool to create a mask for use during a real-time run.

*REQUIRES FSL 5.0+*

The mask MUST match the dimensions and orientation of incoming functional data.
That is, the mask must be in subject functional space.

This tool will transform a selected MNI space mask to subject functional space.
To do so, you must supply:
    - example functional space data from the current subject. This can be a
    a short functional run (~15s) that you've already collected
    - a high resolution anatomical image from the current subject
    - the MNI space mask you wish to transform

Using FSL FLIRT, this tool will create the intermediary transforms to map from MNI-to-HIRES, and HIRES-to-FUNC space, and then combine the transformation
matrices to produce a transform that maps from MNI-to-FUNC. This transformation
will be applied to the specified MNI-space mask or atlas, producing both
binarized and non-binarized versions of the functional space mask.

Lastly, FSLeyes will open and display the results masks for review.

All output will be saved in a subdirectory called 'mask_transforms' located in
the same directory as the example functional space data
"""

import sys
import os
from os.path import join
import time
import yaml

# set the Pyneal root dir. Assumes this tool lives in .../pyneal/utils/
utilsDir = os.path.abspath(os.path.dirname(__file__))
pynealDir = os.path.dirname(utilsDir)

def launchCreateMask():
    """
    Open GUI to modify settings file. Read settings. Build mask accordingly
    """
    ### Read Settings ------------------------------------
    # Read the settings file, and launch the createMask GUI to give the user
    # a chance to update the settings. Hitting 'submit' within the GUI
    # will update the createMaskConfig file with the new settings
    settingsFile = join(utilsDir, 'createMaskConfig.yaml')

    # Launch GUI
    # TODO

    # Read the new settings file, store as dict
    with open(settingsFile, 'r') as ymlFile:
        settings = yaml.load(ymlFile)

    ### Setup output dir and logging
    outputDir = join(os.path.dirname(settings['subjFunc']), 'mask_transforms')
    if not os.path.isdir(outputDir):
        os.makedirs(outputDir)






if __name__ == '__main__':
    launchCreateMask()
