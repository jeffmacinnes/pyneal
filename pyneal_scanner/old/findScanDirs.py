"""
Tools for finding the paths of the scan directories

This is designed to be called from the scanner console itself
-jjm 7/2016
"""
from __future__ import division
from optparse import OptionParser
import sys
import os
import time

######## USER VARIABLES #####################################
ROOT_DIR = '/export/home1/sdc_image_pool/images'


def findChildDirs(parentDir):
	""" 
	return a list of children dir within the specified parent dir
	output: [[path, modification time, size]]
	"""
	# list all of the child directories in the current parent directory
	childDirs = [os.path.join(parentDir, d) for d in os.listdir(parentDir) if os.path.isdir(os.path.join(parentDir, d))]
	if not childDirs:
		print "No subdirectories found in " + parentDir
	else:
		# add the modify time to each directory
		childDirs = [[path, os.stat(path).st_mtime] for path in childDirs]
	return childDirs


def findCurrentExam():
	# find the most recently modified p*/e* folder in the root dir
	parentDir = ROOT_DIR	# initialize the recentDir

	# go 2 levels deep into the root folder
	for depth in range(2):

		# list all of the child directories in the current parent directory
		childDirs = findChildDirs(parentDir)

		# sort based on modification time, take most recent (i.e. largest mtime)
		childDirs = sorted(childDirs, key=lambda x: x[1], reverse=True)
		youngestChild = childDirs[0][0]
		
		# update parent dir
		parentDir = youngestChild

	examDir = '/'.join(parentDir.split('/')[-2:])      #truncate so examDir is just the pXXX/eXXX part
	return examDir


def findSeries(examDir):
	"""
	return a list of all series dirs within the specified exam dir
	output: [[path, modification time]]
	"""
	fullExamPath = os.path.join(ROOT_DIR, examDir)
	seriesDirs = findChildDirs(fullExamPath)

	if seriesDirs:
		# sort based on modification time, oldest to youngest
		seriesDirs = sorted(seriesDirs, key=lambda x: x[1])

	return seriesDirs


# when called directly from the command line.....
if __name__ == '__main__':
	print_option = 0
	
	# set up optional argument parsing (default: entire report printed to the screen)
	parser = OptionParser()
	parser.add_option('-e', '--examDirectory',
						action='store', 
						dest='examDir',
						help='specify the exam directory (FORMAT: pXXX/eXXX; defaults to finding the most recent')
	(options, args) = parser.parse_args()
	if options.examDir is not None:
		examDir = options.examDir		# read the desired exam directory from the input arguments
	else:
		# Get the current exam directory
		examDir = findCurrentExam()

	# get the current series directories
	seriesDirs = findSeries(examDir)

	# print output to the screen
	print '='*15
	print 'Exam Directory: ' 
	print os.path.join(ROOT_DIR, examDir)
	print 'Series:'

	currentTime = int(time.time())
	for s in seriesDirs:
		# get the info from this series
		thisSeries_dirname = s[0].split('/')[-1]
		name_string = '%5s' % thisSeries_dirname
		
		# calculate/format directory size
		thisSeries_size = sum([os.path.getsize(os.path.join(s[0],f)) for f in os.listdir(s[0])])
		if thisSeries_size < 1000:
			size_string = '%5.1f' % thisSeries_size + ' bytes'
		elif 1000 <= thisSeries_size < 1000000:
			size_string = '%5.1f' % float(thisSeries_size/1000) + ' kb'
		elif 1000000 <= thisSeries_size:
			size_string = '%5.1f' % float(thisSeries_size/1000000) + ' mb'

		# calculate time (in mins) since it was modified
		thisSeries_mTime = s[1]
		timeElapsed = currentTime - thisSeries_mTime
		m,s = divmod(timeElapsed, 60)
		time_string = str(int(m)) + 'min ' + str(int(s)) + 's ago'

		print '     ' + '\t'.join([name_string, size_string, time_string])    
	print '='*15
