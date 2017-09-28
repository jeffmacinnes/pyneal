"""
wait4scan.py
-jjm 7/2016

This script will set up the necessary fScan syntax
for transfering files over the socket in real-time.
It will then wait for the scan directory to appear (which occurs once
the scan begins) before submitting the fScan command. 
As such, this script is to be run BEFORE the scan starts
"""

import os
import sys
import time
import json
from optparse import OptionParser
import findScanDirs	# import the findScanDirs.py methods

ROOT_DIR = '/export/home1/sdc_image_pool/images'




if __name__ == '__main__':

	# parse input options
	parser = OptionParser()
	parser.add_option('-d', '--choose_directory', action='store_true', default=False, help='Specify an exam directory')
	(options, args) = parser.parse_args()

	# look for socket settings JSON file, write if needed
	thisDir = os.path.abspath(os.path.dirname(sys.argv[0]))
	socketSettings_fname = os.path.join(thisDir, 'socketSettings.json')
	if os.path.isfile(socketSettings_fname):
		with open(socketSettings_fname) as socket_file:
			socketData = json.load(socket_file)
			destHost = socketData['destHost']
			destPort = socketData['destPort']
	else:
		destHost = raw_input('Enter Destination IP: ')
		destPort = raw_input('Enter Destination Port #: ')
		socketData = {'destHost': destHost, 'destPort': destPort}
		with open(socketSettings_fname, 'w') as socket_file:
			json.dump(socketData, socket_file)

	# Find the exam directory to use
	if options.choose_directory:
		examDir = raw_input('Which Exam Directory? (format: pXXX/eXXX): ')
	else:
		# Find the most recent exam directory
		examDir = findScanDirs.findCurrentExam()

	fullExamDir = os.path.join(ROOT_DIR, examDir)
	print "="*5
	print "Exam Directory: "
	print fullExamDir

	# Get the list of current directory contents
	dirContents = [d for d in os.listdir(fullExamDir)]

	# Wait for a new directory to appear (refresh directory contents, look for new item)
	print "Waiting for new directory to appear..."
	keepWaiting = True
	while keepWaiting:
		for d in os.listdir(fullExamDir):
			if d not in dirContents:
				seriesName = d
				print "New series directory created: " + seriesName
				keepWaiting = False
		time.sleep(0.1)		# wait a 100ms before checking again

	# Pause briefly to ensure the first file has appeared (script will crash if it hasn't)
	time.sleep(1)

	# run the fscan command to send data
	cmd_str = '/usr/local/packages/jvs/bin/fscan ' + os.path.join(fullExamDir, seriesName) + '/' + ' -wait -raw ' + ':'.join([destHost, destPort]) + ' 3'
	print cmd_str
	os.system(cmd_str)
