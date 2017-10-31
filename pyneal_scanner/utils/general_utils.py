"""
Set of general utilities that provide functionality independent of the specific
scanning environment
"""
# python 2/3 compatibility
from __future__ import print_function
if hasattr(__builtins__, 'raw_input'):
    input = raw_input

import os
import sys
from os.path import join

import yaml
import zmq


class ScannerSettings():
    """
    Read the scanner config file to retrieve variables
    that are specific to this scanning environment.

    If no scanner config file exists, user will be prompted to fill in
    values and a config file will be written

    This class contains methods for returning specific configuration settings
    that may be needed by other components of Pyneal
    """

    def __init__(self, settingsDir, config_fname='scannerConfig.yaml'):
        """
        Initialize the class, read yaml config file, create one
        if necessary
        """
        # initialize var to store dict of all of the config parameters
        self.allSettings = None
        self.config_file = join(settingsDir, config_fname)

        # when class is initiated, attempts to find a scanner config file
        # in the specified settingsDir
        if os.path.isfile(self.config_file):
            # open the file, create dict of all scanner settings
            with open(self.config_file, 'r') as ymlFile:
                self.allSettings = yaml.load(ymlFile)
        else:
            # or create the configuration file
            with open(self.config_file, 'w') as ymlFile:
                pass

        # if the yaml config file exists, but is empty, it'll return None.
        # this will make sure self.allSettings is a dict before progressing
        if self.allSettings is None:
            self.allSettings = {}

        # Get the scanner make from the dictionary, and
        # if its not there, prompt user for it
        ### CONSIDER HAVING THIS LOOP OVER ALL REQUIRED SETTINGS
        ### TO CHECK IF THEY EXIST
        if 'scannerMake' not in self.allSettings:
            self.get_scannerMake()


    def print_allSettings(self):
        """
        Print all of the current scanner settings to std.out
        """
        print('='*15)
        print('SCANNER SETTINGS: ')
        for s in self.allSettings:
            print('{}: {}'.format(s, self.allSettings[s]))
        print('='*15)


    def get_scannerMake(self):
        """
        Return the make of the scanner (e.g. GE)
        """
        # check if scannerMake already exists allSettings dict
        if 'scannerMake' in self.allSettings:
            self.scannerMake = self.allSettings['scannerMake']
        else:
            self.scannerMake = self.set_config('scannerMake',
                instructions="type: GE, Phillips, or Siemens")

        # return response
        return self.allSettings['scannerMake']

    def get_scannerSocketHost(self):
        """
        Return the host IP for the socket the scanner should communicate over
        """
        # check if scannerSocketHost already exists in the allSettings dict
        if 'scannerSocketHost' in self.allSettings:
            self.scannerSocketHost = self.allSettings['scannerSocketHost']
        else:
            self.set_config('scannerSocketHost',
                instructions="IP address of machine running real-time analysis")

        # return response
        return self.allSettings['scannerSocketHost']


    def get_scannerSocketPort(self):
        """
        Return the port number for the socket the scanner should communicate over
        """
        # check if scannerSocketPort already exists in the allSettings dict
        if 'scannerSocketPort' in self.allSettings:
            self.scannerSocketPort = self.allSettings['scannerSocketPort']
        else:
            self.set_config('scannerSocketPort',
                instructions='Port # for communicating with real-time analysis machine')

        # return response
        return self.allSettings['scannerSocketPort']


    def get_allSettings(self):
        """
        Return the allSettings dictionary
        """
        return self.allSettings


    def set_config(self, dictKey, instructions=None):
        """
        prompt user for the specified config parameter. [optional] instructions will
        be printed to the screen to show users how to format input.

        The input values supplied by the user will be stored in the
        allSettings dictionary, as well as written to the yaml config file
        """
        # print instructions to user
        print('Please enter the {}'.format(dictKey))
        if instructions is not None:
            print('({}):'.format(instructions))

        # ask for input
        userResponse = input()

        # store the userResponse in allSettings
        self.allSettings[dictKey] = userResponse

        # save the file
        self.writeSettingsFile()

    def writeSettingsFile(self):
        # write the new value to the config file
        with open(self.config_file, 'w') as ymlFile:
            yaml.dump(self.allSettings, ymlFile, default_flow_style=False)


def initializeSession():
    """
    Method that gets called at the beginning of any of the
    pyneal_scanner command line functions. This method will return
    two things:
        - scannerSettings: [object] - Class that reads the current scannerSettings config
                file, or creates one if necessary. Stores all of the current
                scan settings as a dictionary in an attribute named 'allSettings'.
                Contains methods for getting & writing a config file with new
                settings.

        - scannerDirs: [object] - Class that stores all of the relevant dirs and
                path info for a particular scanning environment. The particular
                attributes will vary according to the specific environment.
    """

    # path to the pyneal dir (this assumes this file is stored in a directory
    # one level deeper than the pyneal_scanner dir, AND that this method will only ever
    # be called by command line functions in the pyneal_scanner dir)
    pynealScannerDir = os.path.dirname(os.path.abspath(sys.argv[0]))

    # Intialize the ScannerSettings class. This will take care of reading the
    # config file (if found), or creating one if necessary.
    scannerSettings = ScannerSettings(pynealScannerDir)

    # Initialize the ScannerDirs class. Which flavor of this to load will
    # depend on the particular scanning environment, so check the scannerSettings
    scannerMake = scannerSettings.allSettings['scannerMake']
    if scannerMake == 'GE':
        from utils.GE_utils import GE_DirStructure

        scannerDirs = GE_DirStructure(scannerSettings)

    elif scannerMake == 'Phillips':
        print('no ScannerDirs for Phillips scanners yet...')
    elif scannerMake == 'Siemens':
        print('no ScannerDirs for Siemens scanners yet...')
    else:
        print('Unrecognized Scanner Make: {}'.format(scannerMake))

    return scannerSettings, scannerDirs


def create_scannerSocket(host, port):
    """
    create a zero-mq socket to use for communication between
    pyneal_scanner and a remote source
    """
    context = zmq.Context.instance()
    socket = context.socket(zmq.REQ)
    socket.bind('tcp://{}:{}'.format(host, port))

    return socket
