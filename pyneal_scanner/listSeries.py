"""
(Pyneal-Scanner: Command line function)
Calling this function will print to the terminal all of the series that
are associated with the current session.

Show the name, timestamp, and filesize of each series as a way of helping to
link the series names with phases of your task (e.g. anat scan, task scans)
"""
from __future__ import print_function

from utils.general_utils import initializeSession


if __name__ == '__main__':
    # initialize the session classes:
    scannerSettings, scannerDirs = initializeSession()

    # print all of the current scanner settings to the screen
    scannerSettings.print_allSettings()

    # print all of the current series to the screen
    scannerDirs.print_currentSeries()
