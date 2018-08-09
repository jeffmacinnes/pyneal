import os
from os.path import join
import sys

import yaml

# set up directory structure
testingDir = os.path.dirname(os.path.abspath(__file__))
pynealDir = os.path.dirname(testingDir)
testDataDir = join(testingDir, 'testData')
GE_dir = join(testDataDir, 'GE_env')
GE_funcDir = join(GE_dir, 'p1/e123/s1925')
Philips_dir = join(testDataDir, 'Philips_env')
Philips_funcDir = join(Philips_dir, '0001')
Siemens_dir = join(testDataDir, 'Siemens_env')
Siemens_funcDir = join(Siemens_dir, 'funcData')

sys.path.insert(0, pynealDir)
import pyneal_scanner.utils.general_utils as general_utils


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


class Test_general_utils:
    """ Test pyneal_scanner.utils.general_utils module """

    def test_ScannerSettings(self):

        # test GE
        print(__name__)
        GE_scannerConfig_file = join(GE_dir, 'scannerConfig.yaml')
        replace_scannerConfig_baseDir(GE_scannerConfig_file, GE_funcDir)

        scanSettings = general_utils.ScannerSettings(GE_dir)
        scanSettings.print_allSettings()
        scanSettings.get_scannerMake()
        scanSettings.get_scannerBaseDir()
        scanSettings.get_pynealSocketHost()
        scanSettings.get_pynealSocketPort()
        scanSettings.get_allSettings()

        cleanConfigFile(GE_scannerConfig_file)
