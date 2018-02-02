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
        self.expectedFields = ['scannerBaseDir', 'scannerMake', 'pynealSocketHost', 'pynealSocketPort']

        # when class is initiated, attempts to find a scanner config file
        # in the specified settingsDir
        if os.path.isfile(self.config_file):
            # open the file, create dict of all scanner settings
            with open(self.config_file, 'r') as ymlFile:
                self.allSettings = yaml.load(ymlFile)
        else:
            # or create the configuration file, write empty fields
            with open(self.config_file, 'w') as ymlFile:
                for field in self.expectedFields:
                    ymlFile.write(field + ':')

        # if the yaml config file exists, but is empty, it'll return None.
        # this will make sure self.allSettings is a dict before progressing
        if self.allSettings is None:
            self.allSettings = {}

        # Ensure all settings are present before continuing
        self.get_scannerMake()
        self.get_scannerBaseDir()
        self.get_pynealSocketHost()
        self.get_pynealSocketPort()


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


    def get_scannerBaseDir(self):
        """
        Return the base directory where new data is written for each scan
        """
        # check if scannerBaseDir already exists allSettings dict
        if 'scannerBaseDir' in self.allSettings:
            self.scannerBaseDir = self.allSettings['scannerBaseDir']
        else:
            self.scannerBaseDir = self.set_config('scannerBaseDir',
                instructions="type: GE, Phillips, or Siemens")

        # make sure the base dir exists
        while True:
            if not os.path.isdir(self.scannerBaseDir):
                print('Problem: {} is not an existing directory'.format(self.scannerBaseDir))
                self.scannerBaseDir = self.set_config('scannerBaseDir',
                    instructions="type: GE, Phillips, or Siemens")
            else:
                break

        # return response
        return self.allSettings['scannerBaseDir']


    def get_pynealSocketHost(self):
        """
        Return the host IP for the real-time analysis computer
        """
        # check if pynealSocketHost already exists in the allSettings dict
        if 'pynealSocketHost' in self.allSettings:
            self.pynealSocketHost = self.allSettings['pynealSocketHost']
        else:
            self.set_config('pynealSocketHost',
                instructions="IP address of machine running real-time analysis")

        # return response
        return self.allSettings['pynealSocketHost']


    def get_pynealSocketPort(self):
        """
        Return the port number that the real-time analysis machine is listening on
        """
        # check if pynealSocketPort already exists in the allSettings dict
        if 'pynealSocketPort' in self.allSettings:
            self.pynealSocketPort = self.allSettings['pynealSocketPort']
        else:
            self.set_config('pynealSocketPort',
                instructions='Port # for communicating with real-time analysis machine')

        # return response
        return self.allSettings['pynealSocketPort']


    def get_allSettings(self):
        """
        Return the allSettings dictionary
        """
        return self.allSettings


    def set_config(self, field, instructions=None):
        """
        prompt user for the specified config parameter. [optional] instructions will
        be printed to the screen to show users how to format input.

        The input values supplied by the user will be stored in the
        allSettings dictionary, as well as written to the yaml config file
        """
        # print instructions to user
        print('Please enter the {}'.format(field))
        if instructions is not None:
            print('({}):'.format(instructions))

        # ask for input
        userResponse = input()

        # store the userResponse in allSettings
        self.allSettings[field] = userResponse

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

    elif scannerMake == 'Philips':
        from utils.Philips_utils import Philips_DirStructure
        scannerDirs = Philips_DirStructure(scannerSettings)

    elif scannerMake == 'Siemens':
        from utils.Siemens_utils import Siemens_DirStructure
        scannerDirs = Siemens_DirStructure(scannerSettings)

    elif scannerMake == 'sandbox':
        # UPDATE THIS AS NEEDED FOR DIFFERENT TESTING SCENARIOS
        from utils.GE_utils import GE_DirStructure
        scannerDirs = GE_DirStructure(scannerSettings)

    else:
        print('Unrecognized Scanner Make: {}'.format(scannerMake))

    return scannerSettings, scannerDirs


def create_pynealSocket(host, port):
    """
    create a zero-mq socket to use for communication between
    pyneal_scanner and a remote source where Pyneal is running.
    In this case, Pyneal_scanner is acting as a client making
    an outgoing connection to the server (i.e. Pyneal)
    """
    context = zmq.Context.instance()
    socket = context.socket(zmq.PAIR)
    socket.connect('tcp://{}:{}'.format(host, port))

    return socket
