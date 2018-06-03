""" Set of classes and methods specific to Philips scanning environments

"""
from __future__ import print_function
from __future__ import division

import os
from os.path import join
import sys
import time
import re
import fnmatch
import glob
import json
import logging
from threading import Thread
from queue import Queue

import numpy as np
import nibabel as nib
import argparse
import zmq


class Philips_DirStructure():
    """ Finding the names and paths of series directories in a Philips scanning
    environment

    In Philips environments, using the XTC module for exporting data in
    real-time, data will be exported to a shared directory that is accessible
    from the Pyneal workstation. We'll refer to this shared directory as the
    session directory, and the `sessionDir` variable will refer to the full
    path of that directory.

    Within the `sessionDir` each new series will be assigned it's own
    subdirectory, which we'll refer to as the series dir (`seriesDir`). The
    series dirs will be numbered sequentially in order of creation, starting
    with '0000'.

    Each `seriesDir` will contain Par/Rec file pairs for each volume in the
    series. These file pairs will appear in real-time as the scan progresses.

    This class contains methods to retrieve the most recently modified series
    directories, as well as monitor for the creation of new series directories,
    and stores attributes referring to the directory structure for the current
    scanning session.

    """
    def __init__(self, scannerSettings):
        """ Initialize the class

        Parameters
        ----------
        scannerSettings : object
            class attributes represent all of the settings unique to the
            current scanning environment (many of them read from
            `scannerConfig.yaml`)

        See Also
        --------
        general_utils.ScannerSettings
        """
        # initialize class attributes
        if 'scannerBaseDir' in scannerSettings.allSettings:
            self.baseDir = scannerSettings.allSettings['scannerBaseDir']
        else:
            print('No scannerBaseDir found in scannerConfig file')
            sys.exit()

        self.sessionDir = self.baseDir


    def print_currentSeries(self):
        """ Find all of the series dirs in given sessionDir, and print them
        all, along with time since last modification, and directory size

        """
        # find the sessionDir, if not already found
        if self.sessionDir is None:
            self.findSessionDir()

        # get a list of all series dirs in the sessionDir
        seriesDirs = self._findAllSubdirs(self.sessionDir)

        if seriesDirs is not None:
            # sort based on modification time
            seriesDirs = sorted(seriesDirs, key=lambda x: x[1])

            # print directory info to the screen
            print('Session Dir: ')
            print('{}'.format(self.sessionDir))
            print('Series Dirs: ')

            currentTime = int(time.time())
            for s in seriesDirs:
                # get the info from this series dir
                dirName = s[0].split('/')[-1]

                # add to self.seriesDirs

                # calculate & format directory size
                dirSize = sum([os.path.getsize(join(s[0], f)) for f in os.listdir(s[0])])
                if dirSize < 1000:
                    size_string = '{:5.1f} bytes'.format(dirSize)
                elif 1000 <= dirSize < 1000000:
                    size_string = '{:5.1f} kB'.format(dirSize/1000)
                elif 1000000 <= dirSize:
                    size_string = '{:5.1f} MB'.format(dirSize/1000000)

                # calculate time (in mins/secs) since it was modified
                mTime = s[1]
                timeElapsed = currentTime - mTime
                m,s = divmod(timeElapsed,60)
                time_string = '{} min, {} s ago'.format(int(m),int(s))

                print('    {}\t{}\t{}'.format(dirName, size_string, time_string))


    def _findAllSubdirs(self, parentDir):
        """ Return a list of all subdirectories within the specified
        parentDir, along with the modification time for each

        Parameters
        ----------
        parentDir : string
            full path to the parent directory you want to search

        Returns
        -------
        subDirs : list
            each item in `subDirs` is itself a list containing 2-items for each
            subdirectory in the `parentDir`. Each nested list will contain the
            path to the subdirectory and the last modification time for that
            directory. Thus, `subDirs` is structured like:
                [[subDir_path, subDir_modTime]]

        """
        subDirs = [join(parentDir, d) for d in os.listdir(parentDir) if os.path.isdir(join(parentDir, d))]
        if not subDirs:
            subDirs = None
        else:
            # add the modify time for each directory
            subDirs = [[path, os.stat(path).st_mtime] for path in subDirs]

        # return the subdirectories
        return subDirs


    def waitForSeriesDir(self, interval=.1):
        """ Listen for the creation of a new series directory.

        Once a scan starts, a new series directory will be created
        in the `sessionDir`. By the time this function is called, this
        class should already have the `sessionDir` defined

        Parameters
        ----------
        interval : float, optional
            time, in seconds, to wait between polling for a new directory

        Returns
        -------
        seriesDir : string
            full path to the newly created directory

        """
        startTime = int(time.time())    # tag the start time
        keepWaiting = True
        while keepWaiting:
            # obtain a list of all directories in sessionDir that start with '0'
            childDirs = glob.glob(join(self.sessionDir, '0*'))

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
        return seriesDir


    def get_seriesDirs(self):
        """ Build a list that contains the directory names of all of the
        series directories currently in the `sessionDir`. Set the class
        attribute for `seriesDirs`

        Returns
        -------
        seriesDirs : list
            list of all series directories (directory names ONLY) found within
            the current `sessionDir`

        """
        # get a list of all sub dirs in the sessionDir
        subDirs = self._findAllSubdirs(self.sessionDir)

        if subDirs is not None:
            # extract just the dirname from subDirs and append to a list
            self.seriesDirs = []
            for d in subDirs:
                self.seriesDirs.append(d[0].split('/')[-1])
        else:
            self.seriesDirs = None

        return self.seriesDirs


class Philips_BuildNifti():
    """ Tools to build a 3D or 4D Nifti image from all of the par/rec file
    pairs for a given series

    Input is a path to a series directory containing par/rec file pairs for
    each volume in the series. Image parameters, like voxel spacing and
    dimensions, are obtained automatically from info in the dicom tags

    End result is a Nifti1 formatted 3D (anat) or 4D (func) file in RAS+
    orientation.

    """
    def __init__(self, seriesDir):
        """ Initialize class, and set/obtain basic class attributes like file
        paths and scan parameters

        Parameters
        ----------
        seriesDir : string
            full path to the directory containing the raw par/rec file pairs
            for each volume in the series

        """
        # initialize attributes
        self.seriesDir = seriesDir
        self.niftiImage = None

        # make a list of all of the par files in this dir
        par_pattern = re.compile(fnmatch.translate('*.par'), re.IGNORECASE)
        parFiles = [x for x in os.listdir(self.seriesDir) if par_pattern.match(x)]

        # figure out what type of image this is, 4d or 3d
        self.scanType = self._determineScanType(parFiles[0])

        # build nifti image
        if self.scanType == 'anat':
            self.niftiImage = self.buildAnat(parFiles)
        elif self.scanType == 'func':
            self.niftiImage = self.buildFunc(parFiles)


    def buildAnat(self, parFiles):
        """ Build a 3D structural/anatomical Nifti image from the par/rec file

        On Philip's scanner, entire anat image is assumed to be contained in
        single par/rec file pair. Open the par file, extract the image data,
        realign to RAS+ and build a nifti object

        Parameters
        ----------
        parFiles : list
            list containing the file names (file names ONLY, no path) of all
            par files in a the series directory. If this is an anatomical image
            there should only be a single file in the list

        Returns
        -------
        anatImage_RAS : Nifti1Image
            nifti-1 formated image of the 3D anatomical data, oriented in
            RAS+

        See Also
        --------
        nibabel.nifti1.Nifti1Image()

        """
        # should only be a single parFile in the list
        anatImage = nib.load(join(self.seriesDir,parFiles[0]), strict_sort=True)

        # convert to RAS+
        anatImage_RAS = nib.as_closest_canonical(anatImage)

        print('Nifti image dims: {}'.format(anatImage_RAS.shape))

        return anatImage_RAS

    def buildFunc(self, parFiles):
        """ Build a 4D functional image from list of par files

        Given a list of `parFiles`, build a 4D functional image from them. For
        Philips scanners, there should be a par header file and corresponding
        rec image file for each volume in the series. This function will read
        each header/image pair and construct a 4D nifti object. The 4D nifti
        object contain a voxel array ordered like RAS+ as well the affine
        transformation to map between vox and mm space

        Parameters
        ----------
        parFiles : list
            list containing the file names (file names ONLY, no path) of all
            par files to be used in constructing the final nifti image

        Returns
        -------
        funcImage_RAS : Nifti1Image
            nifti-1 formated image of the 4D functional data, oriented in
            RAS+

        See Also
        --------
        nibabel.nifti1.Nifti1Image()

        """
        imageMatrix = None
        affine = None

        ### Loop over all of the par files
        nVols = len(parFiles)
        for par_fname in parFiles:
            # build full path to this par file
            par_fname = join(self.seriesDir, par_fname)

            # make sure there is a corresponding .rec file
            if not os.path.isfile(par_fname.replace('.par', '.rec')):
                print('No REC file found to match par: {}', par_fname)

            ### Build the 3d voxel array for this volume and reorder to RAS+
            # nibabel will load the par/rec, but there can be multiple images (mag,
            # phase, etc...) concatenated into the 4th dimension. Loading with the
            # strict_sort option (I think) will make sure the first image is the data
            # we want. Extract this data, then reorder the voxel array to RAS+
            thisVol = nib.load(par_fname, strict_sort=True)

            # get the vol index from the acq_nr field of the header (1-based index)
            volIdx = int(thisVol.header.general_info['acq_nr']) - 1

            # convert to RAS+
            thisVol_RAS = nib.as_closest_canonical(thisVol)

            # construct the imageMatrix if it hasn't been made yet
            if imageMatrix is None:
                imageMatrix = np.zeros(shape=(thisVol_RAS.shape[0],
                                            thisVol_RAS.shape[1],
                                            thisVol_RAS.shape[2],
                                            nVols), dtype=np.uint16)

            # construct the affine if it isn't made yet
            if affine is None:
                affine = thisVol_RAS.affine

            # Add this data to the image matrix
            imageMatrix[:, :, :, volIdx] = thisVol_RAS.get_data()[:,:,:,0].astype('uint16')

        ### Build a Nifti object
        funcImage = nib.Nifti1Image(imageMatrix, affine=affine)

        return funcImage


    def _determineScanType(self, parFile):
        """ Figure out what type of scan this is, anat or func

        This tool will determine the scan type from a given par file.
        Possible scan types are either single 3D volume (anat), or a 4D dataset
        built up of 2D slices (func). The scan type is determined by reading
        the `scan_mode` variable within the par header

        Parameters
        ----------
        parFile : string
            file name (not full path) of par file from the current session that
            you would like to open to read the imaging parameters from

        Returns
        -------
        scanType : string
            either 'anat' or 'func' depending on scan type stored in dicom tag

        """
        # read the parfile
        par = nib.load(join(self.seriesDir, parFile), strict_sort=True)
        if par.header.general_info['scan_mode'] == '3D':
            scanType = 'anat'
        elif par.header.general_info['scan_mode'] == '2D':
            scanType = 'func'
        else:
            print('Cannot determine scan type from this image! Check the header')
            sys.exit()

        return scanType


    def get_scanType(self):
        """ Return the scan type """
        return self.scanType


    def get_niftiImage(self):
        """ Return the constructed Nifti Image """
        return self.niftiImage


    def write_nifti(self, output_path):
        """ Write the nifti file to disk

        Parameters
        ----------
        outputPath : string
            full path, including filename, you want to use to save the nifti
            image

        """
        nib.save(self.niftiImage, output_path)
        print('Image saved at: {}'.format(output_path))


class Philips_monitorSeriesDir(Thread):
    """ Class to monitor for new par/rec images to appear in the seriesDir.

    This class will run independently in a separate thread, monitoring a
    specified directory for the appearance of new par files. Each new par
    header file that appears will be added to the Queue for further processing

    """
    def __init__(self, seriesDir, parQ, interval=.2):
        """ Initialize the class, and set basic class attributes

        Parameters
        ----------
        seriesDir : string
            full path to the series directory where new dicom files will appear
        parQ : object
            instance of python queue class to hold new par files before they
            have been processed. This class will add items to that queue.
        interval : float, optional
            time, in seconds, to wait before repolling the seriesDir to check
            for any new files

        """
        # start the thread upon completion
        Thread.__init__(self)

        # set up logger
        self.logger = logging.getLogger(__name__)

        # initialize class parameters
        self.interval = interval            # interval for polling for new files
        self.seriesDir = seriesDir          # full path to series directory
        self.parQ = parQ                    # queue to store par header files
        self.alive = True                   # thread status
        self.numParsAdded = 0               # counter to keep track of # mosaics
        self.queued_par_files = set()       # empty set to store names of queued mosaic
        self.par_pattern = re.compile(fnmatch.translate('*.par'), re.IGNORECASE)
        parFiles =

    def run(self):
        # function that runs while the Thread is still alive
        while self.alive:

            # create a set of all par files currently in the series dir
            #currentPars = set(glob.glob(join(self.seriesDir, '*.par')))
            currentPars = set([join(self.seriesDir, x) for x in os.listdir(self.seriesDir) if self.par_pattern.match(x)])

            # grab only the ones that haven't already been added to the queue
            newPars= [f for f in currentPars if f not in self.queued_par_files]

            # loop over each of the new mosaic files, add each to queue
            for f in newPars:
                par_fname = join(self.seriesDir, f)
                try:
                    self.parQ.put(par_fname)
                except:
                    self.logger.error('failed on: {}'.format(par_fname))
                    print(sys.exc_info())
                    sys.exit()
            if len(newPars) > 0:
                self.logger.debug('Put {} new par files on the queue'.format(len(newPars)))
            self.numParsAdded += len(newPars)

            # now update the set of pars added to the queue
            self.queued_par_files.update(set(newPars))

            # pause
            time.sleep(self.interval)


    def get_numParsAdded(self):
        """ Return the cumulative number of par files added to the queue thus far """
        return self.numParsAdded


    def stop(self):
        """ Set the `alive` flag to False, stopping thread """
        self.alive = False


class Philips_processVolume(Thread):
    """ Class to process each par header file in the queue.

    This class will run in a separate thread. While running, it will pull
    'tasks' off of the queue and process each one. Processing each task
    involves reading the par header file and the corresponding rec binary file,
    extracting the voxel data and relevant header information, reordering it to
    RAS+, and then sending the volume and header out over the pynealSocket

    """
    def __init__(self, parQ, pynealSocket, interval=.2):
        """ Initialize the class

        Parameters
        ----------
        parQ : object
            instance of python queue class that will store the par header file
            names. This class will pull items from that queue.
        pynealSocket : object
            instance of ZMQ style socket that will be used to communicate with
            Pyneal. This class will use this socket to send image data and headers
            to Pyneal during the real-time scan.
            See also: general_utils.create_pynealSocket()
        interval : float, optional
            time, in seconds, to wait before repolling the queue to see if there
            are any new file names to process

        """
        # start the threat upon creation
        Thread.__init__(self)

        # set up logger
        self.logger = logging.getLogger(__name__)

        # initialize class parameters
        self.parQ = parQ
        self.interval = interval        # interval between polling queue for new files
        self.alive = True
        self.pynealSocket = pynealSocket
        self.totalProcessed = 0         # counter for total number of slices processed


    def run(self):
        self.logger.debug('Philips_processVolume started')

        # function to run on loop
        while self.alive:

            # if there are any mosaic files in the queue, process them
            if not self.parQ.empty():
                numParsInQueue = self.parQ.qsize()

                # loop through all mosaics currently in queue & process
                for m in range(numParsInQueue):
                    # retrieve file name from queue
                    par_fname = self.parQ.get(True, 2)

                    # ensure the file has copied completely
                    file_size = 0
                    while True:
                        file_info = os.stat(par_fname)
                        if file_info.st_size == 0 or file_info.st_size > file_size:
                            file_size = file_info.st_size
                        else:
                            break

                    # process this par file
                    self.processParFile(par_fname)

                    # complete this task, thereby clearing it from the queue
                    self.parQ.task_done()

                # log how many were processed
                self.totalProcessed += numParsInQueue
                self.logger.debug('Processed {} tasks from the queue ({} total)'.format(numParsInQueue, self.totalProcessed))

            # pause for a bit
            time.sleep(self.interval)


    def processParFile(self, par_fname):
        """ Process a given par header file

        Read the par header file and corresponding rec image file. Read in as
        a nifti object that will provide the 3D voxel array for this volume.
        Reorder to RAS+, and then send to the pynealSocket

        Parameters
        ----------
        par_fname : string
            full path to the par file that you want to process
        """
        # make sure the corresponding rec file exists
        while not os.path.isfile(par_fname.replace('.par', '.rec')):
            time.sleep(.01)

        ### Build the 3D voxel array and reorder to RAS+
        # nibabel will load the par/rec, but there can be multiple images (mag,
        # phase, etc...) concatenated into the 4th dimension. Loading with the
        # strict_sort option (I think) will make sure the first image is the data
        # we want. Extract this data, then reorder the voxel array to RAS+
        thisVol = nib.load(par_fname, strict_sort=True)

        # get the volume index from the acq_nr field of the header (1-based index)
        volIdx = int(thisVol.header.general_info['acq_nr']) - 1
        self.logger.info('Volume {} processing'.format(volIdx))

        # convert to RAS+
        thisVol_RAS = nib.as_closest_canonical(thisVol)

        # grab the data for the first volume along the 4th dimension
        # and store as contiguous array (required for ZMQ)
        thisVol_RAS_data = np.ascontiguousarray(thisVol_RAS.get_data()[:,:,:,0].astype('uint16'))

        ### Create a header with metadata info
        volHeader = {
            'volIdx': volIdx,
            'dtype': str(thisVol_RAS_data.dtype),
            'shape': thisVol_RAS_data.shape,
            'affine': json.dumps(thisVol_RAS.affine.tolist())
        }

        ### Send the voxel array and header to the pynealSocket
        self.sendVolToPynealSocket(volHeader, thisVol_RAS_data)


    def sendVolToPynealSocket(self, volHeader, voxelArray):
        """ Send the volume data to Pyneal

        Send the image data and header information for the specified volume to
        Pyneal via the `pynealSocket`.

        Parameters
        ----------
        volHeader : dict
            key:value pairs for all of the relevant metadata for this volume
        voxelArray : numpy array
            3D numpy array of voxel data from the volume, reoriented to RAS+

        """
        self.logger.debug('TO pynealSocket: vol {}'.format(volHeader['volIdx']))

        ### Send data out the socket, listen for response
        self.pynealSocket.send_json(volHeader, zmq.SNDMORE) # header as json
        self.pynealSocket.send(voxelArray, flags=0, copy=False, track=False)
        pynealSocketResponse = self.pynealSocket.recv_string()

        # log the success
        self.logger.debug('FROM pynealSocket: {}'.format(pynealSocketResponse))

        # check if that was the last volume, and if so, stop
        if 'STOP' in pynealSocketResponse:
            self.stop()

    def stop(self):
        """ set the `alive` flag to False, stopping the thread """
        self.alive = False


def Philips_launch_rtfMRI(scannerSettings, scannerDirs):
    """ Launch a real-time session in a Philips environment.

    This method should be called from pynealScanner.py before starting the
    scanner. Once called, this method will take care of:
        - monitoring the sessionDir for a new series directory to appear (and
        then returing the name of the new series dir)
        - set up the socket connection to send volume data over
        - creating a Queue to store newly arriving PAR/REC files
        - start a separate thread to monitor the new seriesDir
        - start a separate thread to process PAR/RECs that are in the Queue

    Parameters
    ----------
    scannerSettings : object
        class attributes represent all of the settings unique to the
        current scanning environment (many of them read from
        `scannerConfig.yaml`). Returned from `general_utils.ScannerSettings()``
    scannerDirs : object
        instance of `GE_utils.GE_DirStructure`. Has attributes for the relvant
        paths for the current session. `scannerDirs` is one of the variables
        returned by running `general_utils.initializeSession()`

    See Also
    --------
    general_utils.ScannerSettings()
    general_utils.initializeSession()

    """
    # Create a reference to the logger. This assumes the logger has already
    # been created and customized by pynealScanner.py
    logger = logging.getLogger(__name__)

    #### SET UP PYNEAL SOCKET (this is what we'll use to
    #### send data (e.g. header, slice pixel data) to remote connections)
    # figure out host and port number to use
    host = scannerSettings.get_pynealSocketHost()
    port = scannerSettings.get_pynealSocketPort()
    logger.debug('Scanner Socket Host: {}'.format(host))
    logger.debug('Scanner Socket Port: {}'.format(port))

    # create a socket connection
    from .general_utils import create_pynealSocket
    pynealSocket = create_pynealSocket(host, port)
    logger.debug('Created pynealSocket')

    # wait for remote to connect on pynealSocket
    logger.info('Connecting to pynealSocket...')
    while True:
        msg = 'hello from pyneal_scanner '
        pynealSocket.send_string(msg)
        msgResponse = pynealSocket.recv_string()
        if msgResponse == msg:
            break
    logger.info('pynealSocket connected')

    ### Wait for a new series directory appear
    logger.info('Waiting for new seriesDir...')
    seriesDir = scannerDirs.waitForSeriesDir()
    logger.info('New Series Directory: {}'.format(seriesDir))

    ### Start threads to A) watch for new par/rec files, and B) process
    # them as they appear
    # initialize the par queue to keep store newly arrived
    # par header files, and keep track of which have been processed
    parQ = Queue()

    # create instance of class that will monitor seriesDir. Pass in
    # a copy of the par queue. Start the thread going
    scanWatcher = Philips_monitorSeriesDir(seriesDir, parQ)
    scanWatcher.start()

    # create an instance of the class that will grab par/rec files
    # from the queue, reformat the data, and pass over the socket
    # to pyneal. Start the thread going
    volumeProcessor = Philips_processVolume(parQ, pynealSocket)
    volumeProcessor.start()
