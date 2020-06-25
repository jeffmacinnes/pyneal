""" Set of general utilities that provide functionality independent of the
specific scanning environment

"""
import os
import sys
from os.path import join

import yaml
import zmq


class ScannerSettings():
    """ Read the scanner config file to retrieve variables specific to this
    scanning environment.

    If no scanner config file exists, user will be prompted to fill in
    values and a config file will be written

    This class contains methods for returning specific configuration settings
    that may be needed by other components of Pyneal

    """
    def __init__(self, settingsDir, config_fname='scannerConfig.yaml'):
        """
        Initialize the class, read yaml config file, create one
        if necessary

        Parameters
        ----------
        settingsDir : string
            full path to the Pyneal Scanner settings dir. In most cases this
            will be the pyneal_scanner directory itself, where the
            `scannerConfig.yaml` settings file will be saved
        config_fname : string, optional
            filename to assign to the saved configuration file. Default is
            `scannerConfig.yaml`

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
        """ Print all of the current scanner settings to stdOut

        """
        print('=' * 15)
        print('SCANNER SETTINGS: ')
        for s in self.allSettings:
            print('{}: {}'.format(s, self.allSettings[s]))
        print('=' * 15)

    def get_scannerMake(self):
        """ Return the make of the scanner (e.g. GE)

        Returns
        -------
        string
            scanner make {'GE', 'GEMB', 'Philips', 'Siemens'}

        """
        # add scannerMake, if not already in allSettings
        if 'scannerMake' not in self.allSettings:
            self.set_config('scannerMake',
                            instructions="type: GE, Philips, or Siemens")

        # return setting
        return self.allSettings['scannerMake']

    def get_scannerBaseDir(self):
        """ Return the base directory where new data is written for each scan

        The base directory means slightly different things depending on the
        scanning environment. In all cases, it is the fixed portion of the
        path that remains constant across series

        In a GE environment, the base dir refers to the parent directory on
        the scanner where new session (p###/e###) and series directories (s###)
        will be written into.

        In a Philips environment, the base dir refers to the parent directory
        where new series directories ('####') will appear

        In a Siemens environment, the base dir refers to the parent directory
        where new series files are written to. All of the series files from a
        given session will appear in the same parent directory (or base dir)

        Returns
        -------
        string
            path to base directory used for the current session

        """
        # check if scannerBaseDir already exists allSettings dict
        if 'scannerBaseDir' not in self.allSettings:
            self.set_config('scannerBaseDir',
                            instructions="type: Path to the base directory for new scans")

        # make sure the base dir exists
        while True:
            if not os.path.isdir(self.allSettings['scannerBaseDir']):
                print('Problem: {} is not an existing directory'.format(self.allSettings['scannerBaseDir']))
                self.set_config('scannerBaseDir',
                                instructions="type: Path to the base directory for new scans")
            else:
                break

        # return setting
        return self.allSettings['scannerBaseDir']

    def get_pynealSocketHost(self):
        """ Return the IP address for the socket connection to Pyneal. This
        will most likely be the IP address for the real-time analysis
        workstation running Pyneal.

        Returns
        -------
        string
            IP address for the socket connection hosted by Pyneal

        """
        # check if pynealSocketHost already exists in the allSettings dict
        if 'pynealSocketHost' not in self.allSettings:
            self.set_config('pynealSocketHost',
                            instructions="IP address of computer running real-time analysis")

        # return response
        return self.allSettings['pynealSocketHost']

    def get_pynealSocketPort(self):
        """ Return the port number that Pyneal is using to listen for incoming
        data from Pyneal Scanner.

        Returns
        -------
        string
            port number for communication with Pyneal

        """
        # check if pynealSocketPort already exists in the allSettings dict
        if 'pynealSocketPort' not in self.allSettings:
            self.set_config('pynealSocketPort',
                            instructions='Port # for communicating with real-time analysis computer')

        # return response
        return self.allSettings['pynealSocketPort']

    def get_allSettings(self):
        """ Return the allSettings dictionary

        Returns
        -------
        dictionary
            dictionary containing key:value pairs for all scanner setting for
            the current session

        """
        return self.allSettings

    def set_config(self, field, instructions=None):
        """ Set a given configuration setting

        If a configuration file hasn't been supplied (or if the supplied
        configuration file is missing a critical field) this method will prompt
        the user for the specified config parameter.

        The input values supplied by the user will be stored in the
        allSettings dictionary, as well as written to the new yaml config file

        Parameters
        ----------
        field : string
            name of the configuration parameter that will be set
        instructions : string, optional
            if supplied, the instructions will be printed to the terminal
            before the prompt, thereby telling the user how and what to enter

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
        """ Save the new settings to a configuration yaml file """
        # write the new value to the config file
        with open(self.config_file, 'w') as ymlFile:
            yaml.dump(self.allSettings, ymlFile, default_flow_style=False)


def initializeSession(pynealScannerDir=None):
    """ Initialize a new scanning session for Pyneal Scanner

    Method that gets called at the beginning of most pyneal_scanner command
    line functions, and returns critical settings for configuring Pyneal
    Scanner for the current sessionself.

    Parameters
    ----------
    pynealScannerDir : string, optional
        Path to pyneal_scanner directory, where a `scannerConfig.yaml` file
        is expected. If unspecified, it defaults to setting pynealScannerDir
        to the same directory as the command line function that called this
        method

    Returns
    -------
    scannerSettings : object
        Class that reads the current scannerSettings config file, or creates
        one if necessary. Stores all of the current scan settings as a
        dictionary in an attribute named 'allSettings'. Contains methods for
        getting and writing a config file with new settings.

    scannerDirs: object
        Class that stores all of the relevant dirs and path info for a
        particular scanning session. The particular attributes will vary
        according to the scanner make and current environment.

    """

    if pynealScannerDir is None:
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
    print(scannerMake)
    if scannerMake == 'GE':
        from utils.GE_utils import GE_DirStructure
        scannerDirs = GE_DirStructure(scannerSettings)
    
    elif scannerMake == 'GEMB':
        print('here')
        from utils.GEMB_utils import GE_DirStructure
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
    """ Create a socket that Pyneal Scanner can use to communicate with Pyneal

    Create a zero-mq socket to use for communication between
    pyneal_scanner and a remote source where Pyneal is running.
    In this case, Pyneal_scanner is acting as a client making
    an outgoing connection to the server (i.e. Pyneal)

    Returns
    -------
    socket : object
        Instance of ZMQ style socket that can be used to send and receive
        messages with Pyneal

    """
    context = zmq.Context.instance()
    socket = context.socket(zmq.PAIR)
    socket.connect('tcp://{}:{}'.format(host, port))

    return socket
