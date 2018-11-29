"""Pyneal Real-time fMRI Acquisition and Analysis

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
import glob
import time
import argparse
import subprocess
import atexit
import webbrowser as web

import yaml
import nibabel as nib
import numpy as np
import zmq

from src.pynealLogger import createLogger
from src.scanReceiver import ScanReceiver
from src.pynealPreprocessing import Preprocessor
from src.pynealAnalysis import Analyzer
from src.resultsServer import ResultsServer
import src.GUIs.pynealSetup.setupGUI as setupGUI

# Set the Pyneal Root dir based on where this file lives
pynealDir = os.path.abspath(os.path.dirname(__file__))


def launchPyneal(headless=False, customSettingsFile=None):
    """Main Pyneal Loop.

    This function will launch setup GUI, retrieve settings, initialize all
    threads, and start processing incoming scans

    """
    ### Read Settings ------------------------------------
    # Read the settings file, and launch the setup GUI to give the user
    # a chance to update the settings. Hitting 'submit' within the GUI
    # will update the setupConfig file with the new settings
    if customSettingsFile:
        print('Loading custom settings file: {}'.format(customSettingsFile))
        settingsFile = customSettingsFile
    else:
        settingsFile = join(pynealDir, 'src/GUIs/pynealSetup/setupConfig.yaml')

    if not headless:
        # Launch GUI to let user update the settings file
        setupGUI.launchPynealSetupGUI(settingsFile)
    elif headless:
        print('Running headless...')
        print('Using settings in {}'.format(settingsFile))
        assert os.path.exists(settingsFile), 'Running headless, but settings file does not exist: {}'.format(settingsFile)

    # Read the new settings file, store as dict
    with open(settingsFile, 'r') as ymlFile:
        settings = yaml.load(ymlFile)

    ### Create the output directory, put in settings dict
    outputDir = createOutputDir(settings['outputPath'])
    settings['seriesOutputDir'] = outputDir

    ### Set Up Logging ------------------------------------
    # The createLogger function will do a lot of the formatting set up
    # behind the scenes. You can write to this log by calling the
    # logger var and specifying the level, e.g.: logger.debug('msg')
    # Other modules can write to this same log by calling
    # the command: logger = logging.getLogger('PynealLog')
    logFname = join(outputDir, 'pynealLog.log')
    logger = createLogger(logFname)
    print('Logs written to: {}'.format(logFname))

    # write all settings to log
    for k in settings:
        logger.info('Setting: {}: {}'.format(k, settings[k]))
    print('-'*20)

    ### Launch Threads -------------------------------------
    # Scan Receiver Thread, listens for incoming volume data, builds matrix
    scanReceiver = ScanReceiver(settings)
    scanReceiver.daemon = True
    scanReceiver.start()
    logger.debug('Starting Scan Receiver')

    # Results Server Thread, listens for requests from end-user (e.g. task
    # presentation), and sends back results
    resultsServer = ResultsServer(settings)
    resultsServer.daemon = True
    resultsServer.start()
    logger.debug('Starting Results Server')

    ### Create processing objects --------------------------
    # Class to handle all preprocessing
    preprocessor = Preprocessor(settings)

    # Class to handle all analysis
    analyzer = Analyzer(settings)

    ### Launch Real-time Scan Monitor GUI
    if settings['launchDashboard']:
        ### launch the dashboard app as it's own separate process. Once called,
        # it will set up a zmq socket to listen for inter-process messages on
        # the 'dashboardPort', and will host the dashboard website on the
        # 'dashboardClientPort'
        pythonExec = sys.executable     # path to the local python executable
        p = subprocess.Popen([
                        pythonExec,
                        join(pynealDir,
                             'src/GUIs/pynealDashboard/pynealDashboard.py'),
                        str(settings['dashboardPort']),
                        str(settings['dashboardClientPort'])
                        ])
        # make sure subprocess gets killed at close
        atexit.register(cleanup, p)

        # Set up the socket to communicate with the dashboard server
        context = zmq.Context.instance()
        dashboardSocket = context.socket(zmq.REQ)
        dashboardSocket.connect('tcp://127.0.0.1:{}'.format(settings['dashboardPort']))

        # Open dashboard in browser
        # s = '127.0.0.1:{}'.format(settings['dashboardClientPort'])
        # print(s)
        # web.open('127.0.0.1:{}'.format(settings['dashboardClientPort']))

        # send configuration settings to dashboard
        configDict = {'mask': os.path.split(settings['maskFile'])[1],
                      'analysisChoice': (settings['analysisChoice'] if settings['analysisChoice'] in ['Average', 'Median'] else 'Custom'),
                      'volDims': str(nib.load(settings['maskFile']).shape),
                      'numTimepts': settings['numTimepts'],
                      'outputPath': outputDir}
        sendToDashboard(dashboardSocket,
                        topic='configSettings',
                        content=configDict)

    ### Wait For Scan To Start -----------------------------
    while not scanReceiver.scanStarted:
        time.sleep(.5)
    logger.debug('Scan started')

    ### Set up remaining configuration settings after first volume arrives
    while not scanReceiver.completedVols[0]:
        time.sleep(.1)
    preprocessor.set_affine(scanReceiver.get_affine())

    ### Process scan  -------------------------------------
    # Loop over all expected volumes
    for volIdx in range(settings['numTimepts']):

        ### make sure this volume has arrived before continuing
        while not scanReceiver.completedVols[volIdx]:
            time.sleep(.1)

        ### start timer
        startTime = time.time()

        ### Retrieve the raw volume
        rawVol = scanReceiver.get_vol(volIdx)

        ### Preprocess the raw volume
        preprocVol = preprocessor.runPreprocessing(rawVol, volIdx)

        ### Analyze this volume
        result = analyzer.runAnalysis(preprocVol, volIdx)

        # send result to the resultsServer
        resultsServer.updateResults(volIdx, result)

        ### Calculate processing time for this volume
        elapsedTime = time.time() - startTime

        # update dashboard (if dashboard is launched)
        if settings['launchDashboard']:
            # completed volIdx
            sendToDashboard(dashboardSocket, topic='volIdx', content=volIdx)

            # timePerVol
            timingParams = {'volIdx': volIdx,
                            'processingTime': np.round(elapsedTime, decimals=3)}
            sendToDashboard(dashboardSocket, topic='timePerVol',
                            content=timingParams)

    ### Save output files
    resultsServer.saveResults()
    scanReceiver.saveResults()

    ### Figure out how to clean everything up nicely at the end
    resultsServer.killServer()
    scanReceiver.killServer()


def sendToDashboard(dashboardSocket, topic=None, content=None):
    """ Send a message to the dashboard

    Construct a JSON message using the supplied `topic` and `content`, and send
    it out over the `dashboardSocket` object

    Parameters:
    -----------
    dashboardSocket : zmq socket object
        Instance of dashboard socket class
    topic : string
        Topic type of message to send to Pyneal dashboard. Must be one of the
        expected topic types in order for the dashboard to make sense of it.
        (See: src/GUIs/pynealDashboard/pynealDashboard.py)
    content :
        The actual content you want sent to the dashboard. The `content`
        dtype will vary depending on topic

    """
    if topic is None:
        raise Exception('Dashboard message has topic set to None')
    if content is None:
        raise Exception('Dashboard message has content set to None')

    # format the message to send to dashboard
    msg = {'topic': topic, 'content': content}

    # send
    dashboardSocket.send_json(msg)
    # logger.debug('sent to dashboard: {}'.format(msg))

    # recv the response (should just be 'success')
    response = dashboardSocket.recv_string()
    if response != 'success':
        print(response)
        raise Exception('Could not send this dashboard: {}'.format(msg))
    # logger.debug('response from dashboard: {}'.format(response))


def createOutputDir(parentDir):
    """Create a new output directory

    A new output subdirectory will be created in the supplied parent dir.
    Output directories are named sequentially, starting with pyneal_001. This
    function will find all existing pyneal_### directories in the `parentDir`
    and name the new output directory accordingly.

    Parameters:
    -----------
    parentDir : string
        full path to the parent directory where you'd like the new output
        subdirectory to appear

    Returns:
    --------
    string
        full path to the new output subdirectory

    """
    # find any existing pyneal_### directories, create the next one in series
    existingDirs = glob.glob(join(parentDir, 'pyneal_*'))
    if len(existingDirs) == 0:
        outputDir = join(parentDir, 'pyneal_001')
    else:
        # add 1 to highest numbered existing dir
        nextDirNum = int(sorted(existingDirs)[-1][-3:]) + 1
        outputDir = join(parentDir, 'pyneal_' + str(nextDirNum).zfill(3))

    # create the output dir and return full path to it
    os.makedirs(outputDir)
    return outputDir


def cleanup(pid):
    pid.terminate()
    print('killing process')


### ----------------------------------------------
if __name__ == '__main__':
    # Start Pyneal by calling pyneal.py from the command line
    parser = argparse.ArgumentParser()
    parser.add_argument('--noGUI',
            action='store_true',
            help="run in headless mode, no setup GUI. (requires a valid settings file, either supplied here with -s option, or in {pyneal root}/src/GUIs/pynealSetup.yaml)")
    parser.add_argument('-s', '--settingsFile',
            default=None,
            help="specify the path to a custom settings file")

    args = parser.parse_args()
    launchPyneal(headless=args.noGUI, customSettingsFile=args.settingsFile)
