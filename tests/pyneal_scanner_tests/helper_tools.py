import os
from os.path import join
from os.path import dirname
import sys

def get_pyneal_scanner_test_paths():
    """ Return a dictionary with relevant paths for the pyneal_scanner_tests
    within the `tests` dir
    """
    # set up directory structure
    testingDir = dirname(dirname(os.path.abspath(__file__)))  # path to `tests` dir
    pynealDir = dirname(testingDir)
    testDataDir = join(testingDir, 'testData')
    GE_dir = join(testDataDir, 'GE_env')
    GE_funcDir = join(GE_dir, 'p1/e123')
    Philips_dir = join(testDataDir, 'Philips_env')
    Philips_funcDir = join(Philips_dir, 'funcData')
    Siemens_dir = join(testDataDir, 'Siemens_env')
    Siemens_funcDir = join(Siemens_dir, 'funcData')

    # store paths in dict
    paths = {}
    paths['pynealDir'] = pynealDir
    paths['testDataDir'] = testDataDir
    paths['GE_dir'] = GE_dir
    paths['GE_funcDir'] = GE_funcDir
    paths['Philips_dir'] = Philips_dir
    paths['Philips_funcDir'] = Philips_funcDir
    paths['Siemens_dir'] = Siemens_dir
    paths['Siemens_funcDir'] = Siemens_funcDir

    return paths
