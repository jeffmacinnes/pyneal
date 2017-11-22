"""
Pyneal Logging Module
Tools to set up a logger for a given Pyneal run
"""
# python 2/3 compatibility
from __future__ import print_function

import os
import sys
import logging
import time


def createLogger(log_fName):
    """
    Generic tool to create a logger with preset formatting. Log messages
    will be written to the log file specified by log_fName.

    This method sets up how you want log messages to be formatted for the
    log file, as well as how log messages should be formatted and displayed in
    std.out of the console. You can specifiy a handler for each, along with
    a level, that will determine which messages go where.

    This method will return a logger, but note that once this function has
    been called, any other module can write log messages to this file by
    defining a logger like:
        logger = logging.getLogger(__name__)
    """
    logDir, logFile = os.path.split(log_fName)
    print(logDir)

    # create the log dir if necessary
    if not os.path.isdir(logDir):
        os.makedirs(logDir)

    ### FILE HANDLER - set up how log messages should be formatted in the log file
    fileLogger = logging.FileHandler(log_fName, mode='w')
    fileLogger.setLevel(logging.DEBUG)
    fileLogFormat = logging.Formatter('%(asctime)s - %(levelname)s - %(threadName)s - %(module)s: %(message)s',
                                        '%m-%d %H:%M:%S')
    fileLogger.setFormatter(fileLogFormat)

    ### CONSOLE HANDLER - set up how log messages should appear in std.Out of the console
    consoleLogger = logging.StreamHandler(sys.stdout)
    consoleLogger.setLevel(logging.INFO)
    consoleLogFormat = logging.Formatter('%(threadName)s -  %(message)s')
    consoleLogger.setFormatter(consoleLogFormat)

    ### ROOT LOGGER, add handlers. (subsequent modules can access this same
    # logger by calling: logger = logging.getLogger(__name__)
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)
    logger.addHandler(fileLogger)
    logger.addHandler(consoleLogger)

    # return a reference to this formatted logger
    return logger
