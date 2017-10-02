

"""
Tools for listening for incoming scan data, converting to a standard format,
and sending out via socket
"""
from __future__ import print_function
from builtins import input

import os, sys
from os.path import join
import argparse
import json


def startListening(scanSettings, scanDirectory=None):
    """
    launch interface with scanner, which will listen for incoming
    data, convert it to a standardized format, and send it over the socket
    """
    if scanDirectory:
        print(scanDirectory)




if __name__ == "__main__":
    # parse arguments
    parser = argparse.ArgumentParser()
    parser.add_argument('-d', '--scanDirectory', help="Specify the path to the directory where slice dicoms will be appearing. If not specified, it defaults to a directory determined by the scanner model")
    args = parser.parse_args()

    # look for scannerSettings.json config file, create if needed
    thisDir = os.path.abspath(os.path.dirname(sys.argv[0]))
    scannerSettings_fname = join(thisDir, 'scannerSettings.json')
    if os.path.isfile(scannerSettings_fname):
        print('\nScanner settings loaded from: {}'.format(scannerSettings_fname))
        print('To use different settings, modify or delete this file', end='\n\n')

        # if it exists, open it up and read settings
        with open(scannerSettings_fname) as settings_file:
            settings = json.load(settings_file)
            scannerModel = settings['scannerModel']
            socketHost = settings['socketHost']
            socketPort = settings['socketPort']

        print('Scanner Model: {}'.format(scannerModel))
        print('Destination IP: {}'.format(socketHost))
        print('Socket Port: {}'.format(socketPort))

    else:
        print('\nNo scannerSettings.json file found in {} \n'.format(thisDir))
        print('Enter settings manually:')
        scannerModels = ['GE', 'Phillips', 'Siemens']
        for i in sorted(scannerModels):
            print('{}'.format(scannerModels[i]))
        scannerSelection = input('Scanner Model: ')
        socketHost = input('Enter Destination IP: ')
        socketPort = input('Enter Port #: ')

        # write data to scannerSettings.json file
        settings = {'scannerModel':scannerModels[scannerSelection],
                    'socketHost': socketHost,
                    'socketPort': socketPort}
        with open(scannerSettings_fname, 'w') as settings_file:
            json.dump(settings, settings_file)

    # Start listening for scans
    startListening(settings, args.scanDirectory)
