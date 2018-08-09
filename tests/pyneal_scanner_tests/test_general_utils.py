import os
from os.path import join
import sys

import yaml
import helper_tools

# get dictionary with relevant paths for tests within this module
paths = helper_tools.get_pyneal_scanner_test_paths()
sys.path.insert(0, paths['pynealDir'])

import pyneal_scanner.utils.general_utils as general_utils


### Functions for updating and cleaning the test scannerConfig.yaml files
def replace_scannerConfig_baseDir(configFile, newBaseDir):
    """ Write newBaseDir to the ScannerBaseDir field of given scannerConfig file

    In order to run these tests, the `scannerConfig.yaml` file for every
    scanner enviorment in the testData directory needs to be updated to reflect
    the local path to the scannerBaseDir. Since that varies depending on where
    this test is being run from, this function will swap out that field with
    the current path base on the local path to the pynealDir
    """
    # read in contents of existing yaml file
    with open(configFile, 'r') as ymlFile:
        configSettings = yaml.load(ymlFile)

    # update with new setting
    configSettings['scannerBaseDir'] = newBaseDir

    # overwrite yaml file
    with open(configFile, 'w') as ymlFile:
        yaml.dump(configSettings, ymlFile, default_flow_style=False)


def cleanConfigFile(configFile):
    """ Remove local paths from scannerConfig file.

    After testing, remove the local path to the scannerBaseDir to it does
    not get pushed to gitHub
    """
    with open(configFile, 'r') as ymlFile:
        configSettings = yaml.load(ymlFile)

    # clear existing scannerBaseDir
    configSettings['scannerBaseDir'] = ' '

    # overwrite yaml file
    with open(configFile, 'w') as ymlFile:
        yaml.dump(configSettings, ymlFile, default_flow_style=False)


### Tests for classes/functions within the general_utils.py module. Where
#   applicable, test against each of the different scanner environments
class Test_general_utils:
    """ Test pyneal_scanner.utils.general_utils module """

    def test_ScannerSettings(self):
        """ test general_utils.ScannerSettings() class

        Test methods in ScannerSettings class against sample data from each
        scanner make
        """
        # loop over the different scan environments
        for scanEnv in ['GE', 'Philips', 'Siemens']:
            print('testing environment: ' + scanEnv)

            # set paths based on current test environment
            if scanEnv == 'GE':
                envDir = paths['GE_dir']
                funcDir = paths['GE_funcDir']
            elif scanEnv == 'Philips':
                envDir = paths['Philips_dir']
                funcDir = paths['Philips_funcDir']
            elif scanEnv == 'Siemens':
                envDir = paths['Siemens_dir']
                funcDir = paths['Siemens_funcDir']

            # update config file to match local paths
            configFile = join(envDir, 'scannerConfig.yaml')
            replace_scannerConfig_baseDir(configFile, funcDir)

            # run through all functions in ScannerSettings class
            scanSettings = general_utils.ScannerSettings(envDir)
            scanSettings.print_allSettings()
            scanSettings.get_scannerMake()
            scanSettings.get_scannerBaseDir()
            scanSettings.get_pynealSocketHost()
            scanSettings.get_pynealSocketPort()
            scanSettings.get_allSettings()

            # remove local paths from config file
            cleanConfigFile(configFile)

            print('Passed!')
