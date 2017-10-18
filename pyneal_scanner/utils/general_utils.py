"""
Set of General Utilities that provide functionality independent of the specific
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


class ScannerSettings():
    """
    Read the scanner config file to retrieve variables
    that are specific to this scanning environment.

    If no scanner config file exists, user will be prompted to fill in
    values and a config file will be written
    """

    def __init__(self, settingsDir, config_fname='scannerConfig.yaml'):
        """
        Initialize the class, read yaml config file, create one
        if necessary
        """
        # initialize var to store dict of scannerSettings
        self.scannerSettings = None
        self.config_file = join(settingsDir, config_fname)

        # when class is initiated, attempts to find a scanner config file
        # in the specified settingsDir
        if os.path.isfile(self.config_file):
            # open the file, create dict of all scanner settings
            with open(self.config_file, 'r') as ymlFile:
                self.scannerSettings = yaml.load(ymlFile)
        else:
            # create a file
            with open(self.config_file, 'w') as ymlFile:
                pass
        if self.scannerSettings is None:
            self.scannerSettings = {}


    def get_scannerMake(self):
        """
        Return the make of the scanner (e.g. GE)
        """
        # check if scannerMake already exists scannerSettings dict
        if 'scannerMake' in self.scannerSettings:
            self.scannerMake = self.scannerSettings['scannerMake']
        else:
            self.scannerMake = self.set_scannerSetting('scannerMake',
                instructions="type: GE, Phillips, or Siemens")

        # return response
        return self.scannerSettings['scannerMake']

    def get_socketHost(self):
        """
        Return the host IP for the socket the scanner should communicate over
        """
        # check if socketHost already exists in the scannerSettings dict
        if 'socketHost' in self.scannerSettings:
            self.socketHost = self.scannerSettings['socketHost']
        else:
            self.set_scannerSetting('socketHost',
                instructions="IP address of machine running real-time analysis")

        # return response
        return self.scannerSettings['socketHost']


    def get_socketPort(self):
        """
        Return the port number for the socket the scanner should communicate over
        """
        # check if socketPort already exists in the scannerSettings dict
        if 'socketPort' in self.scannerSettings:
            self.socketPort = self.scannerSettings['socketPort']
        else:
            self.set_scannerSetting('socketPort',
                instructions='Port # for communicating with real-time analysis machine')

        # return response
        return self.scannerSettings['socketPort']

    def set_scannerSetting(self, dictKey, instructions=None):
        """
        prompt user for the specified parameter. [optional] instructions will
        be printed to the screen to show users how to format input.

        The input values supplied by the user will be stored in the
        scannerSettings dictionary, as well as written to the yaml config file
        """
        # print instructions to user
        print('Please enter the {}'.format(dictKey))
        if instructions is not None:
            print('({}):'.format(instructions))

        # ask for input
        userResponse = input()

        # store the userResponse in scannerSettings
        self.scannerSettings[dictKey] = str(userResponse)

        # write the new value to the config file
        with open(self.config_file, 'w') as ymlFile:
            yaml.dump(self.scannerSettings, ymlFile, default_flow_style=False)
