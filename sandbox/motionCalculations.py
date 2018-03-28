import os
from os.path import join
import sys
import io
import contextlib

import time
import numpy as np
from nipy.algorithms.registration import HistogramRegistration, Rigid
import nibabel as nib



@contextlib.contextmanager
def nostdout():
    save_stdout = sys.stdout
    sys.stdout = io.StringIO()
    yield
    sys.stdout = save_stdout


def estimateMotion(refVol, vol, T_estimate):
    """
    input vols should be nibabel Nifti1 images
    """
    reg = HistogramRegistration(vol, refVol, interp='tri')
    T = reg.optimize(T_estimate, maxiter=1, maxfun=35, ftol=1)

    return T


def testMotion():
    # load an example functional image
    img = nib.load('tests/GE_func_s1925.nii.gz')


    # create a reference volume and a test volume
    affine = img.affine

    refVol = img.get_data()[:,:,:,0]
    refVol = nib.Nifti1Image(refVol, affine)

    prevEstimate = Rigid(np.eye(4))

    times = []
    # loop over each volume
    for volIdx in range(img.shape[3]):
        if volIdx == 4:
            refVol = img.get_data()[:,:,:,0]
            refVol = nib.Nifti1Image(refVol, affine)
        elif volIdx > 4:
            thisVol = img.get_data()[:,:,:,volIdx]
            thisVol = nib.Nifti1Image(thisVol, affine)

            # calculate motion
            startTime = time.time()
            with nostdout():
                newT = estimateMotion(refVol, thisVol, prevEstimate)

            #print('translation: {}'.format(newT.translation))
            #print('rotation: {}'.format(newT.rotation))

            # print time
            endTime = time.time()-startTime
            print('vol {} took: {}ms'.format(volIdx, endTime*1000))
            times.append(endTime)

            prevEstimate = newT

    print('Average Time: {}'.format(np.mean(times)))


if __name__ == '__main__':
    testMotion()
