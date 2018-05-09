"""
Simulate the output from pynealScanner.
During a real-time scan, pynealScanner will send data to pyneal over a socket
connection. Each tranmission comes in 2 phases: first a json header with metadata
about the volume, then the volume itself. This tool will emulate that same behavior

You can either supply real 4D image data (as .nii/.nii.gz), or use this tool
to generate a fake dataset of random values.

Set the scan parameters below to indicate the dimensions of your
simulated data (i.e. slice dimensions, number of slices per volume,
number of timepts)
"""
# python 2/3 compatibility
from __future__ import print_function
from __future__ import division
from builtins import input

import os
import time
import json
import argparse

import zmq
import numpy as np
import nibabel as nib


def prepRealDataset(image_path):
    """
    read in the supplied 4d image file, set to RAS+
    returns nibabel like dataset obj
    """
    print('Prepping dataset: {}'.format(image_path))
    ds = nib.load(image_path[0])

    # make sure it's RAS+
    ds_RAS = nib.as_closest_canonical(ds)

    print('Dimensions: {}'.format(ds_RAS.shape))
    return ds_RAS


def prepRandomDataset(dims):
    """
    build a random dataset of shape dims.
    build RAS affine (just identiy matrix here)
    return nibabel like dataset obj
    """
    ('Prepping randomized dataset')
    fakeDataset = np.random.randint(low=1000,
                        high=3000,
                        size=(dims[0],
                        dims[1],
                        dims[2],
                        dims[3]),
                        dtype='uint16' )
    affine = np.eye(4)
    ds = nib.Nifti1Image(fakeDataset, affine)

    print('Randomized Dataset')
    print('Dimensions: {}'.format(ds.shape))
    return ds


def pynealScannerSimulator(dataset, TR=1000, host='127.0.0.1', port=5555):
    """
    simulate Pyneal Scanner by sending the supplied dataset to Pyneal via
    socket one volume at a time. Rate set by 'TR' argument. Each volume
    preceded with a json header with metadata about volume, just like during
    a real scan
    """
    print('TR: {}'.format(TR))
    # convert TR to sec (the unit of time.sleep())
    TR = TR/1000

    # Create socket, bind to address
    print('Connecting to Pyneal at {}:{}'.format(host, port))
    context = zmq.Context.instance()
    socket = context.socket(zmq.PAIR)
    socket.connect('tcp://{}:{}'.format(host, port))

    ds_array = dataset.get_data()
    ds_affine = dataset.affine

    # Wait for pyneal to connect to the socket
    print('waiting for connection...')
    while True:
        msg = 'hello from pynealScanner_sim'
        socket.send_string(msg)

        resp = socket.recv_string()
        if resp == msg:
            print('connected to pyneal')
            break

    # Press Enter to start sending data
    input('Press ENTER to begin the "scan" ')

    # Start sending data!
    for volIdx in range(ds_array.shape[3]):
        startTime = time.time()

        # grab this volume from the dataset
        thisVol = np.ascontiguousarray(ds_array[:,:,:,volIdx])

        # build header
        volHeader = {
                'volIdx': volIdx,
                'dtype':str(thisVol.dtype),
                'shape':thisVol.shape,
                'affine': json.dumps(ds_affine.tolist())
                }

        # send header as json
        socket.send_json(volHeader, zmq.SNDMORE)

        # now send the voxel array for this volume
        socket.send(thisVol, flags=0, copy=False, track=False)
        print('Sent vol: {}'.format(volIdx))

        # list for response
        socketResponse = socket.recv_string()
        print('Socket Response: {}'.format(socketResponse))

        if TR is not None:
            elapsedTime = time.time()-startTime
            time.sleep(TR-elapsedTime)


# run from command line
if __name__ == '__main__':
    # parse arguments
    parser = argparse.ArgumentParser(description="Pyneal-Scanner Simulator",
                                formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('-f', '--filePath',
                        nargs=1,
                        help='path to 4D nifti file')
    parser.add_argument('-r', '--random',
                        action='store_true',
                        help='flag to generate random data')
    parser.add_argument('-d', '--dims',
                        nargs=4,
                        default=[64,64,18,60],
                        help='dimensions of randomly generated dataset [x y z t]')
    parser.add_argument('-t', '--TR',
                        default=1000,
                        type=int,
                        help='TR (in ms)')
    parser.add_argument('-sh', '--sockethost',
                        default='127.0.0.1',
                        help='Pyneal socket host')
    parser.add_argument('-sp', '--socketport',
                        default=5555,
                        help='Pyneal socket port')
    args = parser.parse_args()

    # Prep data, real or fake
    if args.filePath:
        dataset = prepRealDataset(args.filePath)
    else:
        dataset = prepRandomDataset(args.dims)

    # run pynealScanner Simulator
    pynealScannerSimulator(dataset,
                            TR=args.TR,
                            host=args.sockethost,
                            port=args.socketport)
