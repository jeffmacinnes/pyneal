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
import logging
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
    def __init__(self, seriesDir, dicomQ, interval=.5):
        # start the thead upon creation
        Thread.__init__(self)

        # initialize class parameters
        self.interval = interval            # interval for looping the thread
        self.seriesDir = seriesDir          # full path to series directory
        self.dicomQ = dicomQ                # queue to store dicom files
        self.alive = True                   # thread status
        self.numSlicesAdded = 0             # counter to keep track of # of slices added overall
        self.dicom_files = set()            # empty set to store names of processed dicoms

    def run(self):
        # function that loops while the Thead is still alive
        while self.alive:

            # create a set of all dicoms currently in the series directory
            currentDicoms = set(os.listdir(self.seriesDir))

            # grab only the the dicoms which haven't already been added to the queue
            newDicoms = currentDicoms.intersection_update(self.dicom_files)
            #newDicoms = [f for f in currentDicoms if f not in self.dicom_files]

            # add all of the new dicoms to the queue
            for f in newDicoms:
                dicom_fname = join(self.seriesDir, f)
                try:
                    self.dicomQ.put(dicom_fname)
                except:
                    print('failed on: {}'.format(dicom_fname))
                    print(sys.exc_info())
                    sys.exit()
            print('PUT Thread: Put {} new slices on the queue'.format(len(newDicoms)))
            self.numSlicesAdded += len(newDicoms)

            # now update the set of dicoms added to the queue
            self.dicom_files.update(set(newDicoms))

            # pause
            time.sleep(self.interval)

    def get_numSlicesAdded(self):
        return self.numSlicesAdded

    def stop(self):
        # function to stop the Thread
        print('Stopped listening for new slices')
        self.alive = False


class GE_processSlice(Thread):
    """
    Class to process each dicom slice in the dicom queue
    """
    def __init__(self, dicomQ):
        # start the thread upon creation
        Thread.__init__(self)

        # initialize class parameters
        self.dicomQ = dicomQ
        self.alive = True
        print('processSlice Started....')

    def run(self):
        # function to run on loop
        while self.alive:

            # if there are any slices in the queue, process them
            if not self.dicomQ.empty():
                self.numSlicesInQueue = self.dicomQ.qsize()
                print('GET Thread: There are {} items in queue'.format(self.numSlicesInQueue))

                # loop through all slices currently in queue & process
                for s in range(self.numSlicesInQueue):
                    dcm_fname = self.dicomQ.get(True, 2)    # retrieve the filename from the queue
                    dcmFile = dicom.read_file(dcm_fname)
                    sliceNum = dcmFile.InStackPositionNumber
                    volNum = int(dcmFile.InstanceNumber/dcmFile.ImagesInAcquisition)
                    print('GET Thread: processed vol {}, slice {}'.format(volNum, sliceNum))
                    #print('Removed {} from queue'.format(thisFile))
                    self.dicomQ.task_done()  # complete the task on this item in the queue

            time.sleep(.5)

    def stop(self):
        # function to stop the Thread
        print('Stopped processing slices')
        self.alive = False


def startScanRead(sessionDir):
    """
    create an instance of the appropriate scanRead class, initialize
    a queue to store incoming dicom files, and start listening!
    """

    # initialize the dicom queue to keep track of dicom slice files
    dicomQ = Queue()

    # wait for series directory to be created
    seriesDir = waitForSeriesDir(sessionDir)

    #### Start threads to listen for new slices,
    #### and to process each slice
    # create an instance of the class to monitor for GE-style scans
    scanRead = GE_scanRead(seriesDir, dicomQ)
    scanRead.start()

    # create an instance of the class to process each slice
    processSlice = GE_processSlice(dicomQ)
    processSlice.start()

    # TMP -- for testing
    keepListening = True
    while keepListening:
        numSlicesAdded = scanRead.get_numSlicesAdded()
        print('MAIN Thread: {} total slices so far'.format(numSlicesAdded))
        if numSlicesAdded >= 9900:
            print('MAIN Thread: Got enough slices: {}'.format(numSlicesAdded))
            scanRead.stop()
            scanRead.join()     # wait til all tasks on this thread are complete

            processSlice.stop()
            processSlice.join() # wait til all tasks on this thread are complete

            #dicomQ.join()      # blocks until all tasks complete
            scanRead.join()     # wait for the thread to exit

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

    # set up logging
    logging.basicConfig(filename="./GE_scanRead.log",
                        filemode='w',
                        level=logging.DEBUG)

    # parse arguments
    parser = argparse.ArgumentParser()
    parser.add_argument('sessionDir',
                        help="Path to the session directory (i.e. where new series directories are written)")
    # retrieve the args
    args = parser.parse_args()
    logging.info('Listening for new data in: {}'.format(args.sessionDir))

    # start listeing for scan data
    startScanRead(args.sessionDir)
