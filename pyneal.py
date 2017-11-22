"""
Pyneal Real-time fMRI Acquisition and Analysis

This is the main Pyneal application, designed to be called directly from the
command line on the computer designated as your real-time analysis machine.
It expects to receive incoming slice data from the Pyneal-Scanner application,
which should be running concurrently elsewhere (e.g. on the scanner console
itself)

Once this application is called, it'll take care of opening the
GUI, loading settings, launching separate threads for monitoring and analyzing
incoming data, and hosting the Analysis output server
"""
# python 2/3 compatibility
from __future__ import print_function

import os
import sys
from os.path import join
import time

import yaml
from src.scanReceiver import ScanReceiver
from src.pynealLogger import createLogger

# Set the Pyneal Root dir based on where this file lives
pynealDir = os.path.abspath(os.path.dirname(__file__))


def launchPyneal():
    # read settings
    nTmpts = 100
    host = '127.0.0.1'
    port = 5555

    # launch set-up GUI, which SHOWS settings and gives option
    # to CHANGE & SAVE SETTINGS

    ### Set Up Logging ------------------------------------
    # The createLogger function will do a lot of the formatting set up
    # behind the scenes. You can write to this log by calling the
    # logger var and specifying the level, e.g.: logger.debug('msg')
    # Other modules can write to this same log by calling
    # logger = logging.getLogger(__name__)
    logFname = join(pynealDir, 'logs/pynealLog.log')
    logger = createLogger(logFname)

    ### Launch Threads -------------------------------------
    # Scan Receiver Thread, listens for incoming slice data, builds matrix
    scanReceiver = ScanReceiver(nTmpts=nTmpts, host=host, port=port)
    scanReceiver.daemon = True
    scanReceiver.start()
    logger.debug('Starting Scan Receiver')

    ### Wait For Scan To Start -----------------------------
    # The completedSlices table will stay 'None' until first slice arrives
    while True:
        if scanReceiver.completedSlices is not None:
            logger.debug('Scan started')
            break
        time.sleep(.5)

    # Loop over all expected volumes
    for volIdx in range(nTmpts):
        # check if all slices for this volume have arrived yet
        while True:
            if all(scanReceiver.completedSlices[:,volIdx]):
                logger.info('vol {} has arrived'.format(volIdx))
                break
            time.sleep(.1)

    # shutdown thread
    scanReceiver.stop()


### ----------------------------------------------
if __name__ == '__main__':
    launchPyneal()
