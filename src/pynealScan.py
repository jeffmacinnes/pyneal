#!/usr/bin/env python
"""
pynealScan.py
REAL TIME FMRI DATA ACQUISITON

"""

import os
import sys
import fnmatch
import glob
import numpy as np
import time
import re
import struct
import array
import stats
import motion
import preproc
import threading
import datetime
from socket import *

version = 'Pyneal - Real-time fMRI Analysis'

pyneal_dir, src_dir = os.path.split(os.path.abspath(os.path.dirname(sys.argv[0])))
SRC_dir = os.path.join(pyneal_dir, 'src')
GUI_dir = os.path.join(pyneal_dir, 'src/GUIs')
DATA_dir = os.path.join(pyneal_dir, 'data')
LOG_dir = os.path.join(pyneal_dir, 'data/logs')

# add relevant paths to the search path
for d in [SRC_dir, GUI_dir]:
	sys.path.append(d)

# import modules in each of those directories
from server import *
from receiver import *
from pynealScanGUI import *
from log_window import *
from plotter import *


### OPEN GUI, PROMPT USER FOR CONFIG VALUES ### ***********************************************************************************
user_gui = PynealScanGUI(pyneal_dir)						# creates instance of UserGUI (opens UserGUI, asks for config settings).
if user_gui.submitted == False:								# don't continue if the SUBMIT button wasn't ever hit
	sys.exit()
													
host = user_gui.host_setting
in_port = int(user_gui.in_port_setting)						# Port number for incoming data
out_port = int(user_gui.out_port_setting)					# Port number for outgoing data
n_tmpts = int(user_gui.n_tmpts_setting)						# number of time pts in total
preproc_choice = user_gui.preproc_choice_setting			# the choice of whether to take raw voxel values or run an incremental GLM
roi_choice = user_gui.roi_choice_setting				    # choice of ROI (whether Mask or Defined)
stat_choice = user_gui.stat_choice_setting					# Stat choice
log_choice = user_gui.log_choice_setting					# the choice for whether to write a log or not
save_choice = user_gui.save_choice_setting					# the choice for whether to save the output or not
plot_choice = user_gui.plot_choice_setting					# the choice for whether to plot the motion or not
coordinates = user_gui.coordinates							# the list of coordinates to be included in the analysis
weights = user_gui.weights									# the list of weights corresponding to each voxel in the ROI (1 unless otherwise specified)
stat_dict = {1:'mean ROI signal', 2:'median ROI signal', 3:'custom stat script'}

# print options to command window
print 'Local host: ' + host
print 'Incoming Port #: ' + str(in_port)
print 'Outgoing Port #: ' + str(out_port)
print 'expected volumes: ' + str(n_tmpts)
if roi_choice == 1:
	print 'ROI choice: Mask'
	print 'Voxel Weighting? (0=no; 1=yes): ' + str(user_gui.mask_wt_choice_setting)
print '# voxels in ROI: ' + str(len(coordinates))
if len(coordinates) < 50:
	print 'Coordinates (x, y, z): ' + str(coordinates)
else:
	print 'Coordinates (x,y,z): ' + str(coordinates[:50]) + '... (truncated)'
print 'Stat Type: ' + stat_dict[stat_choice]
print 'Plot Motion: ' + str(plot_choice)

### INITIAL SETUP ### ******************************************************************
sys.path.append(pyneal_dir)						# add pyneal path to python search space

# create log dir if not already made	
if log_choice == 1:
	date = str(datetime.datetime.now()).replace(' ', '_').replace(':', '-')[:-10]
	log_name = os.path.join(LOG_dir, (date + '_CONFIG.txt'))						# build log name based on current datetime

output_values = np.zeros(n_tmpts)				# preallocate a variable to store output values
volume_complete_times = np.zeros(n_tmpts)		# preallocate a variable to store the time it takes to calculate each volume
volume_start_times = np.zeros(n_tmpts)			# preallocate a variable to store the time when each volume started

# initialize the motion plot if specified
if plot_choice == 1:
	motion_plot = Plotter(plot_title='Motion Plot', data_labels=['X', 'Y', 'Z'], n_Ys=3, Xrange=np.array([0,n_tmpts]))

### IN-SCRIPT FUNCTIONS ### ****************************************************************************************
# Open the log file, write the specified log message, close log file
def write_log(text_to_write, log_name):
	""" Open log file, write the specified text to it, close """
	log_message = (time.asctime() + ' ----- ' + text_to_write + '\n' )
	log_file = open(log_name, 'a')
	log_file.write(log_message)
	log_file.close()

def write_output(text_to_write, output_fname):
	data_file = open(output_fname, 'a')
	message = (text_to_write + '\n')
	data_file.write(message)
	data_file.close()
	
def pynealShutdown():
	print 'Shutting down...'
	receiver.close_socket()												# close the receiver socket
	server.close_socket()												# close the server socket
	statOutputLog.close_pipe()											# close the analysis output x11 window
	motion_plot.close_plot()											# close the motion plot
	sys.exit()

# write to log if requested
if log_choice == 1:
	write_log(version, log_name)
	write_log(('n_tmpts: ' + str(n_tmpts)), log_name)
	write_log(('local hostname: ' + host), log_name)
	write_log(('incoming port #: ' + str(in_port)), log_name)
	write_log(('outgoing port #: ' + str(out_port)), log_name)
	if preproc_choice == 1:
		write_log('Preprocessing: None (raw values)', log_name)
	elif preproc_choice == 2:
		write_log('Preprocessing: IncGLM', log_name)
		write_log(('GLM Design file: ' + user_gui.loaded_design_setting), log_name)
		write_log(('mean regressor included?: ' + str(user_gui.mean_regressor_choice_setting)), log_name)
		write_log(('motion regressors included?: ' + str(user_gui.motion_regressors_choice_setting)), log_name)
	if roi_choice == 1:
		write_log('ROI type: Mask', log_name)
		write_log(('Mask name: ' + user_gui.mask_name), log_name)
		write_log(('Allow weighting?: ' + str(user_gui.mask_wt_choice_setting)), log_name)
	elif roi_choice == 2:
		write_log('ROI type: Defined Sphere', log_name)
		write_log(('Center (x, y, z): ' + str(user_gui.roi_cx) + ' ' + str(user_gui.roi_cy) + ' ' + str(user_gui.roi_cz)), log_name)
		write_log(('Radius (mm): ' + str(user_gui.roi_rad)), log_name)
	if stat_choice == 1:
		write_log('Stat Choice: Average', log_name)
	elif stat_choice == 2:
		write_log('Stat Choice: Median', log_name)
	elif stat_choice == 3:
		write_log('Stat Choice: Custom', log_name)
		write_log(('Custom stat script: ' + user_gui.loaded_custom_stat_script_setting), log_name)
	write_log(('# of voxels in ROI: ' + str(len(coordinates))), log_name)
	write_log(('Coordinates (x, y, z): ' + str(coordinates)), log_name)
	write_log(('save output: ' + str(save_choice)), log_name)
	write_log(('plot motion: ' + str(plot_choice)), log_name)


### INITIALIZE PREPROC & STAT OPTIONS ### **************************************************************************
# create an instance of the Session preproc class with the appropriate options
if preproc_choice == 1:												# if RAW values
	session_preproc = preproc.SessionPreproc(preproc_choice)
elif preproc_choice == 2:											# if Incremental GLM
	session_preproc = preproc.SessionPreproc(preproc_choice,
	 							coordinates=coordinates,
								design=user_gui.design_matrix, 
								mean_choice=user_gui.mean_regressor_choice_setting,
								motion_choice=user_gui.motion_regressors_choice_setting)

# create an instance of the RealtimeStats class with the appropriate options
if stat_choice == 1:
	session_stats = stats.SessionStats(stat_choice, coordinates=coordinates, weights=weights)
elif stat_choice == 2:
	session_stats = stats.SessionStats(stat_choice, coordinates=coordinates)
elif stat_choice == 3:
	session_stats = stats.SessionStats(stat_choice, coordinates=coordinates, stat_script=user_gui.loaded_custom_stat_script_setting)

### BEGIN REAL-TIME ### **********************************************************************************
# open logging window
statOutputLog = LogWindow('Analysis Output')
statOutputLog.write_log('Stat Output:')

# start the receiver and server
receiver = Receiver(host, in_port, n_tmpts)							# create an instance of the Receiver class
receiver.start()													# start the thread. Waits for incoming images
server = Server(host, out_port)										# create an instance of the Server class
server.start()														# start the thread. Answers requests for information

# Wait for images to begin appearing
try:
	while True:
		time.sleep(.5)
		if receiver.get_last_completed_vol() > 0:
			start = time.time()
			break
except KeyboardInterrupt:
	pynealShutdown()

# Loop through every volume that is expected
most_recent_vol = 0
for vol in range(1, n_tmpts+1):												# for every volume (vol here is vol #, NOT index location)
	try:
		while True:
			time.sleep(.001)
			most_recent_vol = receiver.get_last_completed_vol()				# make sure the requested volume has arrived
			if most_recent_vol >= vol:break
	except KeyboardInterrupt:
		pynealShutdown()
		break		
			
	# retrieve raw volume
	raw_volume = receiver.get_volume(vol)
	
	# record volume start time
	volume_start_times[vol-1] = time.time()
	
	# plot and calculate motion
	if plot_choice == 1:
		if vol == 1:
			motion_reference = motion.CenterOfMass(raw_volume)						# set the first volume as reference 
			motion_plot.update_plot(np.array([0,0,0]))								# motion plots start at 0 for all directions
		else:
			motion_change = motion.calculate_motion(raw_volume, motion_reference)	# compute the motion relative to reference vol
			motion_plot.update_plot(motion_change)
	
	# run preprocessing on raw volume
	preproc_volume = session_preproc.run_preproc(raw_volume)
		
	# run stats on preprocessed volume
	stat_output = session_stats.run_stats(preproc_volume)
	
	# append stat output to session output list, update server thread
	output_values[vol-1] = stat_output
	server.update_server(most_recent_vol, output_values)				# let the server know which volumes have arrived
	
	# print stat output to log window
	statOutputLog.write_log(('volume ' + str(vol) + ' stat_output: ' + str(stat_output)))
	
	# record volume complete time
	volume_complete_times[vol-1] = time.time()
	
end = time.time()

# calculate time elapsed for each volume
volume_start_times = receiver.get_volume_start_times()
time_per_volume = volume_complete_times - volume_start_times

print 'total time: ', str(end-start)
print 'analysis-time/volume: ', str(np.mean(time_per_volume)), ' (avg); ', str(np.median(time_per_volume)), ' (med)'
	
# write the output values to file if requested
if save_choice == 1:
	date = str(datetime.datetime.now()).replace(' ', '_').replace(':', '-')[:-10]
	output_fname = os.path.join(log_dir, (date + '_OUTPUT.txt'))
	for value in output_values:
		write_output(str(value), output_fname)

# write to log if requested
if log_choice == 1:
	write_log(('Start time: ' + str(start)), log_name)
	write_log(('Finish time: ' + str(end)), log_name)
	write_log(('Total time: ' + str(end-start)), log_name)
	write_log(('Time/vol: ' + str((end-start)/n_tmpts)), log_name)		

# Wait for user input before quitting
raw_input('press ENTER to quit')

pynealShutdown()




