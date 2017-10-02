"""
Tool for listening for incoming slice data from GE scanners.

Temp tool for testing out routines. Once this works, fold into the
a more general pyneal_scanner.py script
"""

from __future__ import print_function

import os, sys
from os.path import join
import argparse
import dicom
from queue import Queue

import time
from threading import Thread


#### ADD A LOGGER TO ALL OF THIS

class GE_scanRead(Thread):
    """
    Class to monitor for new slices images on GE scanner.
    Once a new series directory is identified, it will watch
    for new slice dicoms to appear. Each new dicom file will
    be added to the Queue for further processing
    """
    def __init__(self, seriesDir, dicomQ, interval=.1):
        # start the thead upon creation
        Thread.__init__(self)

        # initialize class parameters
        self.interval = interval            # interval for looping the thread
        self.seriesDir = seriesDir          # full path to series directory
        self.dicomQ = dicomQ        # queue to store dicom files
        self.alive = True                   # thread status
        self.dicom_files = set()            # initialize empty set to store dicoms


    def run(self):
        # function that loops while the Thead is still alive
        while self.alive:

            # grab all dicoms in the series directory
            currentDicoms = os.listdir(self.seriesDir)

            # figure out which haven't already been added to the queue
            newDicoms = [f for f in currentDicoms if f not in self.dicom_files]
            print('found {} new dicoms'.format(len(newDicoms)))

            # add all of the new dicoms to the
            for f in newDicoms:
                self.dicomQ.put(f)

            # now update the set of dicoms added to the queue
            self.dicom_files.update(set(newDicoms))

            # pause
            time.sleep(self.interval)


    def nSlicesAdded(self):
        return self.dicomQ.qsize()


    def stop(self):
        # function to stop the Thread
        print('Stopped listening for new slices')
        self.alive = False




def startScanRead(sessionDir):
    """
    create an instance of the appropriate scanRead class, initialize
    a queue to store incoming dicom files, and start listening!
    """

    # initialize the dicom queue
    dicomQ = Queue()

    # wait for series directory to be created
    seriesDir = waitForSeriesDir(sessionDir)

    # create an instance of the class to monitor for GE-style scans
    scanRead = GE_scanRead(seriesDir, dicomQ)
    scanRead.start()


    # TMP -- for testing
    keepListening = True
    while keepListening:
        nSlicesAdded = scanRead.nSlicesAdded()
        if nSlicesAdded >= 10:
            print('Got enough slices: {}'.format(nSlicesAdded))
            scanRead.stop()

            dicomQ.join()      # blocks until all tasks complete
            scanRead.join()

            keepListening = False

        #
        time.sleep(.5)







def waitForSeriesDir(sessionDir, interval=.1):
    """
    listen for the creation of a new series directory
    sessionDir should be the full path to the directory where new series
    directories appear for each scan within a session.
        e.g. on GE systems, a session dir may take the form of:
            /export/home1/sdc_image_pool/images/p3/e131

    Once this function is called, the NEXT directory to be modified or created
    within the sessionDir will be considered to be the seriesDir for this scan
    """
    print('Waiting for series directory to appear...')

    startTime = int(time.time())    # tag the start time

    keepWaiting = True
    while keepWaiting:
        # obtain a list of all directories in sessionDir
        childDirs = [join(sessionDir, d) for d in os.listdir(sessionDir) if os.path.isdir(join(sessionDir, d))]

        # loop through all dirs, check modification time
        for thisDir in childDirs:
            thisDir_mTime = os.path.getmtime(thisDir)
            if thisDir_mTime > startTime:
                seriesDir = thisDir
                keepWaiting = False
                break

        # pause before searching directories again
        time.sleep(interval)

    # return the found series directory
    print('New Series Directory: {}'.format(seriesDir))
    return seriesDir



if __name__ == "__main__":
    # parse arguments
    parser = argparse.ArgumentParser()
    parser.add_argument('sessionDir',
                        help="Path to the session directory (i.e. where new series directories are written)")
    # retrieve the args
    args = parser.parse_args()

    # start listeing for scan data
    startScanRead(args.sessionDir)
