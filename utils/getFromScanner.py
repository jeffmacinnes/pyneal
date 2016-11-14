"""
getFromScanner.py
-jjm 7/2016

Retrieve completed runs from the scanner. 
This script will ssh to the scanner, and then run a script to list the current scan series.

At the prompt, type which series you'd like. Then, at the next prompt, type the name you'd like to give to this series. 

The script will use scp to copy the desired data from the scanner to the local directory: /Users/Shared/rtfMRI/experiment_data
"""

import os
import re
import sys
import json
import pexpect
import getpass
from optparse import OptionParser


def listCurrentExamDir(scannerInfo):
	""" ssh to the scanner, run: 
			python findCurrentScans.py -e 
		to retrieve the exam directory for the current scan
	"""
	### SSH VARS
	scanner_user = scannerInfo['scannerUser']
	scanner_host = scannerInfo['scannerHost']
	passoword = scannerInfo['scannerPassword']
	ssh_str = 'ssh %s@%s' % (scanner_user, scanner_host)

	SSH_NEWKEY = '(?i)are you sure you want to continue connecting'
	COMMAND_PROMPT = scanner_user+'@.*[$%>]'	   # possible command prompts

	# Open the connection
	child = pexpect.spawn(ssh_str)
	i = child.expect([pexpect.TIMEOUT, SSH_NEWKEY, '(?i)password'])		# 3 possible options: timeout, no public key cached, asks for password
	if i == 0:
		print "ERROR: COULD NOT SSH"
		print child.before + ' ' + child.after
		sys.exit(1)
	if i == 1:							# No public key cached yet
		child.sendline('yes')			# Accept the public key
		child.expect('(?i)password')
		child.sendline(password)		# Send password
	if i == 2:
		child.sendline(password)        # Send password
	child.expect(COMMAND_PROMPT)

	# grab current exam directory
	cmd_str = 'python ' + scannerScriptsDir + '/findScanDirs.py'		# command to be run to retrieve just the exam directory
	child.sendline(cmd_str)
	child.expect(COMMAND_PROMPT)

	# get the exam dir from the stdout
	examDirPattern = re.compile(r".*\/p\d*\/e\d*")		# regular expression to look for single line ending in 'p<digits>/e<digits>'
	output = child.before
	foundPattern = re.search(examDirPattern, output)
	if foundPattern:
		examDir = foundPattern.group()
		examDir = '/'.join(examDir.split('/')[-2:])

		# close the connection
		child.close()
		return examDir
	else:
		print "Cannot find the current exam directory"
		child.close()
		return None

def listSeries(examDir, scannerInfo):
	scanner_user = scannerInfo['scannerUser']
	scanner_host = scannerInfo['scannerHost']
	passoword = scannerInfo['scannerPassword']
	ssh_str = 'ssh %s@%s' % (scanner_user, scanner_host)

	### SSH VARS
	SSH_NEWKEY = '(?i)are you sure you want to continue connecting'
	COMMAND_PROMPT = scanner_user+'@.*[$%>]'	   # possible command prompts
	
	# Open the connection
	child = pexpect.spawn(ssh_str)
	i = child.expect([pexpect.TIMEOUT, SSH_NEWKEY, '(?i)password'])		# 3 possible options: timeout, no public key cached, asks for password
	if i == 0:
		print "ERROR: COULD NOT SSH"
		print child.before + ' ' + child.after
		sys.exit(1)
	if i == 1:							# No public key cached yet
		child.sendline('yes')			# Accept the public key
		child.expect('(?i)password')
		child.sendline(password)		# Send password
	if i == 2:
		child.sendline(password)        # Send password

	# print full output to the screen for reference
	cmd_str = 'python ' + scannerScriptsDir + '/findScanDirs.py -e ' + examDir	# command to be run once in
	child.expect(COMMAND_PROMPT)		# wait for connection to be established	
	child.sendline(cmd_str)         	# Send command
	child.expect(COMMAND_PROMPT)

	# format output before printing to screen (this was just trial and error)
	print '='*10
	print 'Exam Directory: '
	print os.path.join(scannerSrcDir, examDir)
	print ''
	seriesPattern = re.compile(r"s\d{1,}.*")     	# match all 's' followed by 1 or more digits and then everything after
	output = child.before
	foundPatterns = re.findall(seriesPattern, output)
	print 'Series:'
	for s in foundPatterns:
		print '\t' + s
	print '='*10


def constructFiles(examDir, seriesName, outputDir, outputName, scannerInfo):
	"""
	ssh to the scanner, use fscan to build .img/.hdr pair from raw slice data. 
	The 'rtfmri' user account does not have write permission anywhere except home folder, 
	so the .img/.hdr pair have to be written to and copied from there.

		examDir: the pXXX/eXXX part of the current scan directory
		seriesName: the sXXX part of the current scan directory
		outputDir: local scanner directory to temporarily write the constructed files to
		outputName: the filename, without prefix, for the output files
		scannerInfo: dict with login infomation to the scanner
	"""
	scanner_user = scannerInfo['scannerUser']
	scanner_host = scannerInfo['scannerHost']
	passoword = scannerInfo['scannerPassword']
	ssh_str = 'ssh %s@%s' % (scanner_user, scanner_host)

	print 'building .img/.hdr pair...'

	### SSH VARS
	COMMAND_PROMPT = scanner_user + '@.*[$%>]'	   # possible command prompts
	seriesDir = os.path.join(scannerSrcDir, examDir, seriesName)
	cmd_str = fscan + ' ' + seriesDir + '/*.1 -o ' + os.path.join(localTempDir,outputName) + '.hdr -h'	# fscan command to build 
	#print cmd_str

	# SSH in
	child = pexpect.spawn(ssh_str)
	
	# send password
	child.expect('(?i)password')		# ask for password
	child.sendline(password)
	child.expect(COMMAND_PROMPT)

	# send command
	child.sendline(cmd_str)
	child.expect(COMMAND_PROMPT, timeout=240)

	# close the connection
	child.close()

def copyFiles(fName, sourceDir, destDir, scannerInfo):
	"""
	Copy the desired files from the localTempDir on the scanner to the destination directory
		fName: filename, without extension, to copy
		soureDir: diretory where files currently are
		destDir: directory where files are to be copied to
		scannerInfo: dict with login infomation to the scanner
	"""
	scanner_user = scannerInfo['scannerUser']
	scanner_host = scannerInfo['scannerHost']
	passoword = scannerInfo['scannerPassword']
	ssh_str = 'ssh %s@%s' % (scanner_user, scanner_host)

	### SSH VARS
	#COMMAND_PROMPT = scanner_user + '@.*[$%>]'	   # possible command prompts
	remoteAccount = '%s@%s' %(scanner_user, scanner_host)
	sourceFiles = os.path.join(sourceDir, (fName + '.*'))
	cmd_str = 'scp ' + remoteAccount + ':' + sourceFiles + ' ' + destDir + '/'

	#print cmd_str

	# send the scp command
	child = pexpect.spawn(cmd_str)

	# send password
	child.expect('(?i)password')		# ask for password
	child.sendline(password)

	# wait for command prompt
	child.expect(pexpect.EOF)

	# close the connection
	child.close()


def cleanupFiles(fName, sourceDir, scannerInfo):
	"""
	delete the specified files from the source directory

		fName: filename, without extension
		sourcedir: the local scanner dir where the files reside
		scannerInfo: dict with login infomation to the scanner
	"""
	scanner_user = scannerInfo['scannerUser']
	scanner_host = scannerInfo['scannerHost']
	passoword = scannerInfo['scannerPassword']
	ssh_str = 'ssh %s@%s' % (scanner_user, scanner_host)

	### SSH VARS
	COMMAND_PROMPT = '.*[$%>]'	   # possible command prompts

	# build command
	sourceFiles = os.path.join(sourceDir, (fName + '.*'))
	cmd_str = 'rm ' + sourceFiles 

	# SSH in
	child = pexpect.spawn(ssh_str)
	
	# send password
	child.expect('(?i)password')		# ask for password
	child.sendline(password)
	child.expect(COMMAND_PROMPT)

	# send command
	child.sendline(cmd_str)
	child.expect(COMMAND_PROMPT)

	# close the connection
	child.close()


####### CONFIG VARS
destDir = '/Users/Shared/rtfMRI/experiment_data'				# biac5 dir where the files will be copied to
scannerSrcDir = '/export/home1/sdc_image_pool/images'			# scanner parent dir for exam/series directorires, and raw slice data
scannerScriptsDir = '/usr/local/packages/pyneal'				# scanner dir with local pyneal scripts
localTempDir = '/export/home/rtfmri/expData'						# scanner dir for temporarily writing files to and copying from
fscan = '/usr/local/packages/jvs/bin/fscan'						# full path to fscan command on scanner

if __name__ == '__main__':

	# parse input options (if any)
	parser = OptionParser()
	parser.add_option('-d', '--choose_directory', action='store_true', default=False, help='Override the default behavior of copying from the most recent exam directory. This option will prompt you to specify an exam directory')
	(options, args) = parser.parse_args()

	# look for socket settings JSON file, write if needed
	thisDir = os.path.abspath(os.path.dirname(sys.argv[0]))
	scannerLogin_fname = os.path.join(thisDir, 'scannerLogin.json')
	if os.path.isfile(scannerLogin_fname):
		with open(scannerLogin_fname) as login_file:
			loginData = json.load(login_file)
			scanner_user = loginData['scannerUser']
			scanner_host = loginData['scannerHost']
	else:
		print 'Enter login info for scanner (<user>@<host>)'
		scanner_user = raw_input('Enter User: ')
		scanner_host = raw_input('Enter Host: ')
		loginData = {'scannerUser': scanner_user, 'scannerHost': scanner_host}
		with open(scannerLogin_fname, 'w') as login_file:
			json.dump(loginData, login_file)
	scanner_password = []

	# Set the password for access to the scanner using the rtfmri@biac5-mr account
	if not scanner_password:
		scanner_password = getpass.getpass("Please enter the password for " + "@".join([scanner_user, scanner_host]) + ': ')
	loginData['scannerPassword'] = scanner_password

	# Find the exam directory to use
	if options.choose_directory:
		examDir = raw_input('Which Exam Directory? (format: pXXX/eXXX): ')
	else:
		examDir = listCurrentExamDir(loginData)

	# List the Series available in the selected exam directory
	listSeries(examDir, scanner_password)

	while True:
		# Prompt for series number
		desiredSeries = raw_input('Which Series Name? (format: sXXX): ')
		desiredName = raw_input('What Output Name? (e.g. FUNC# or ANAT): ')

		# Build the desired files
		constructFiles(examDir, desiredSeries, localTempDir, desiredName, scanner_password)

		# Copy the files
		copyFiles(desiredName, localTempDir, destDir, scanner_password)

		# Clean up the files
		cleanupFiles(desiredName, localTempDir, scanner_password)

		# Report
		print 'Copy of ' + desiredSeries + ' complete...'

		# ask for more files
		doAgain = raw_input('Copy more files? [y]/n  ')
		if doAgain == 'n':
			break
