"""
Set of classes and methods specific to GE scanning environments
"""
from __future__ import print_function

import os
from os.path import join
import sys
import time


GE_baseDir = '/export/home1/sdc_image_pool/images'


class GE_DirStructure():
    """
    Methods for finding a returning the names and paths of
    series directories in a GE scanning environment

    In GE enviroments, a new folder is created for every series (i.e. each
    unique scan). The series folders are typically named like 's###'. While
    the number for the first series cannot be predicted, subsequent series
    directorie tend to (but not necessarily, it turns out) be numbered
    sequentially

    All of the series directories for a given session (or 'exam' in GE-speak)
    are stored in an exam folder, named like 'e###', where the number is
    unpredictable. Likewise, each exam folder is stored in a parent folder,
    named like 'p###' where the number is unpredictable. The p### directories
    are stored in a baseDir which (thankfully) tends to be a fixed path.

    So, in other words, new series show up in a unique directory with an
    absolute path like:
    [baseDir]/p###/e###/s###

    Throughout, we'll sometimes refer to the directory that contains
    the s### directories as the 'sessionDir'. So,

    sessionDir = [baseDir]/p###/e###

    This class contains methods to retrieve THE MOST RECENTLY modified
    sessionDir directories, as well as a list of all s### directories along
    with timestamps and directory sizes. This will hopefully allow users to
    match a particular task scan (e.g. anatomicals, or experimentRun1) with
    the full path to it's raw data on the scanner console
    """
    def __init__(self, baseDir=GE_baseDir):

        # initialize the class attributes
        self.baseDir = baseDir
        self.sessionDir = None
        self.pDir = None
        self.eDir = None
        self.seriesDirs = {}

        # try to find the sessionDir first
        self.sessionDir = self.findSessionDir()

        print('BaseDir: {}'.format(self.baseDir))
        print('Session Dir: {}'.format(self.sessionDir))


    def findSessionDir(self):
        """
        Find the most recently modified p###/e### directory in the
        baseDir
        """

        try:
            # Find all subdirectores in the baseDir
            pDirs = self._findAllSubdirs(self.baseDir)

            # sort based on modification time, take the most recent
            pDirs = sorted(pDirs, key=lambda x: x[1], reverse=True)
            newest_pDir = pDirs[0][0]

            ### ADD SOME ERROR CHECKING TO MAKE SURE DIRS START WITH P

            # Now, find the most recent e### dir in the same manner
            eDirs = self._findAllSubdirs(newest_pDir)
            eDirs = sorted(eDirs, key=lambda x: x[1], reverse=True)
            newest_eDir = eDirs[0][0]

            sessionDir = newest_eDir
        except:
            print('Could not find the session dir')
            sessionDir = None

        return sessionDir

    def _findAllSubdirs(self, parentDir):
        """
        Return a list of all subdirectories within the specified
        parentDir, along with the modification time for each

        output: [[subDir_path, subDir_modTime]]
        """
        subDirs = [join(parentDir, d) for d in os.listdir(parentDir) if os.path.isdir(join(parentDir, d))]
        if not subDirs:
            subDirs = None
        else:
            # add the modify time for each directory
            subDirs = [[path, os.stat(path).st_mtime] for path in subDirs]

        # return the subdirectories
        return subDirs






    def test(self):
        print('heyya')
