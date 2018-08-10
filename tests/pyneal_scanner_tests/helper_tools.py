import os
from os.path import join
from os.path import dirname
import sys

import yaml

def get_pyneal_scanner_test_paths():
    """ Return a dictionary with relevant paths for the pyneal_scanner_tests
    within the `tests` dir
    """
    # set up directory structure
    testingDir = dirname(dirname(os.path.abspath(__file__)))  # path to `tests` dir
    pynealDir = dirname(testingDir)
    pynealScannerDir = join(pynealDir, 'pyneal_scanner')
    testDataDir = join(testingDir, 'testData')
    GE_dir = join(testDataDir, 'GE_env')
    GE_funcDir = GE_dir
    Philips_dir = join(testDataDir, 'Philips_env')
    Philips_funcDir = join(Philips_dir, 'funcData')
    Siemens_dir = join(testDataDir, 'Siemens_env')
    Siemens_funcDir = join(Siemens_dir, 'funcData')

    # store paths in dict
    paths = {}
    paths['pynealDir'] = pynealDir
    paths['pynealScannerDir'] = pynealScannerDir
    paths['testDataDir'] = testDataDir
    paths['GE_dir'] = GE_dir
    paths['GE_funcDir'] = GE_funcDir
    paths['Philips_dir'] = Philips_dir
    paths['Philips_funcDir'] = Philips_funcDir
    paths['Siemens_dir'] = Siemens_dir
    paths['Siemens_funcDir'] = Siemens_funcDir

    return paths


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
