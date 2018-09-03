import os
from os.path import join
import sys
import importlib.util

import nibabel as nib
import numpy as np

import pyneal_helper_tools as helper_tools

# get dictionary with relevant paths for tests within this module
paths = helper_tools.get_pyneal_test_paths()
if paths['pynealDir'] not in sys.path:
        sys.path.insert(0, paths['pynealDir'])

print(sys.path)
spec = importlib.util.spec_from_file_location("mkDummyMask.mkDummyMask",
            join(paths['pynealDir'], 'utils/mkDummyMask.py'))
mkDummyMask = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mkDummyMask)


def test_mkDummyMask():
    """ test pyneal.utils.mkDummyMask """
    # inputs
    x = 64
    y = 64
    z = 20
    outputPath = paths['testDataDir']

    # make the mask
    mkDummyMask.mkDummyMask([x,y,z], outputPath)

    # load the mask
    maskName = 'dummyMask_{}-{}-{}.nii.gz'.format(x,y,z)
    mask = nib.load(join(outputPath, maskName))

    # confirm mask dims
    assert mask.shape == (x,y,z)

    # confirm mask size within volume
    # (mask should by 16x16 -- .25*x x .25*y -- so 256 voxels
    # in the middle slice only)
    mask_array = mask.get_data()
    assert np.sum(mask_array) == 256           # confirm total
    assert np.sum(mask_array[:,:,int(z/2)]) == 256  # confirm it comes from middle slice

    # remove the newly created mask
    os.remove(join(outputPath, maskName))
