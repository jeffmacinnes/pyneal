#!/usr/bin/env python
# encoding: utf-8
"""
custom_ROI_covariance.py

custom stat script to calculate the covariance between 2 ROIs

-jjm 2012-07-24
"""

import sys
import os
import numpy as np
import time
import datetime
import stats
from select_ROIs_GUI import *

######### CUSTOM STAT CLASS
class CustomStatClass:
	"""
	This is a template file to write custom statistical scripts. 
	Place your custom code within the specified area below. 
	"""
	
	def __init__(self, coordinates):
		""" INSERT CODE TO BE EXECUTED BEFORE RUN BEGINS"""		
		# any files in the same directory as your custom stat script will be added to your path
		self.class_dir = os.path.abspath(os.path.dirname(__file__))
		sys.path.append(self.class_dir)
		###############################################################################
		################# INSERT USER-SPECIFIED CODE BELOW ############################
		
		# ACCESS TO VOXEL COORDS FROM ROI SPECIFIED BY GUI 
		# (FEEL FREE TO COMMENT OUT IF NOT NEEDED)
		#self.coordinates = coordinates
		
		# set up log parameters to write the session settings to
		self.log_dir = os.path.join(self.pyneal_dir, 'logs', 'custom_stat_logs')
		if not os.path.isdir(self.log_dir):
			os.mkdir(self.log_dir)
		date = str(datetime.datetime.now()).replace(' ', '_').replace(':', '-')[:-10]
		self.log_name = os.path.join(self.log_dir, (date + '_CUSTOM_STAT.txt'))
		self.write_log(('script name: ' + os.path.basename(__file__)), self.log_name)
		
		# open GUI to get coordinates for each ROI
		selection_gui = ROI_selections()
		self.r1_roi_choice = selection_gui.r1_roi_choice_setting
		self.r1_coords = selection_gui.r1_coords
		self.r1_weights = selection_gui.r1_weights
		self.r2_roi_choice = selection_gui.r2_roi_choice_setting
		self.r2_coords = selection_gui.r2_coords
		self.r2_weights = selection_gui.r2_weights
				
		# write ROI options to log
		self.write_log(('ROI 1 type: ' + str(self.r1_roi_choice)), self.log_name)
		if self.r1_roi_choice == 1:
			self.write_log(('ROI 1 filename: ' + str(selection_gui.r1_current_mask_setting)), self.log_name)
			self.write_log(('ROI 1 # voxels: ' + str(selection_gui.r1_mask_n_nonzero_vox_setting)), self.log_name)
			self.write_log(('ROI 1 weighted?: ' + str(selection_gui.r1_mask_wt_choice_setting)), self.log_name)
		self.write_log('ROI 1 coordinates:', self.log_name)
		self.write_log(str(self.r1_coords), self.log_name)
		self.write_log('ROI 1 weights:', self.log_name)
		self.write_log(str(self.r1_weights), self.log_name)
		self.write_log(('ROI 2 type: ' + str(self.r2_roi_choice)), self.log_name)
		if self.r2_roi_choice == 1:
			self.write_log(('ROI 2 filename: ' + str(selection_gui.r2_current_mask_setting)), self.log_name)
			self.write_log(('ROI 2 # voxels: ' + str(selection_gui.r2_mask_n_nonzero_vox_setting)), self.log_name)
			self.write_log(('ROI 2 weighted?: ' + str(selection_gui.r2_mask_wt_choice_setting)), self.log_name)
		self.write_log('ROI 2 coordinates:', self.log_name)
		self.write_log(str(self.r2_coords), self.log_name)		
		self.write_log('ROI 2 weights:', self.log_name)
		self.write_log(str(self.r2_weights), self.log_name)
		
		# set covarianace window (i.e. how many timepts to calculate covariance over)
		self.cov_window = 5
		
		# initialize volume counter index at 0
		self.volume_count = 0
		
		# initialize arrays to store ROI values for each volume (NOTE: could be faster with preallocation here)
		self.r1_vals = np.zeros(1000) 
		self.r2_vals = np.zeros(1000)

		################# END USER-SPECIFIED CODE ############################
		###############################################################################
		

	def compute_stats(self, volume, coordinates):
		""" 
		INSERT CODE TO BE EXECUTED ON EACH VOLUME AS IT ARRIVES
		
		Note: the final output of any calculations must be stored in 
		a variable named 'self.stat_output'
		"""
		###############################################################################
		################# INSERT USER-SPECIFIED CODE BELOW ############################
		
		# add new ROI-1 average to the list of r1_vals
		#self.r1_vals[self.volume_count] = self.get_average_ROI(volume, self.r1_coords, self.r1_weights)
		
		# add new ROI-2 average to the list of r2_vals
		#self.r2_vals[self.volume_count] = self.get_average_ROI(volume, self.r2_coords, self.r2_weights)
		
		# compute covariance between ROIs 
		#if self.volume_count >= self.cov_window:
		#	window_range = np.arange(self.volume_count-self.cov_window, self.volume_count, 1)
		#	cov_matrix = np.corrcoef(self.r1_vals[window_range], self.r2_vals[window_range])
		#	self.stat_output = np.round(cov_matrix[0,1], decimals=3)
		#else:
		#	self.stat_output = 0
		
		#self.r1_val = self.get_average_ROI(volume, self.r1_coords, self.r1_weights)
		self.r2_val = self.get_average_ROI(volume, self.r2_coords, self.r2_weights)
		
		self.stat_output = self.r2_val
		
		
		# increment the volume count
		self.volume_count = self.volume_count + 1	

		################# END USER-SPECIFIED CODE ############################
		###############################################################################
		return self.stat_output
		
	def get_average_ROI(self,volume, ROI_coords, ROI_weights):
		""" return the weighted mean from the ROI specified by the ROI_coords """
		voxel_vals = np.zeros(len(ROI_coords))
		for index, vox_location in enumerate(ROI_coords):
			voxel_vals[index] = self.get_voxel(volume, vox_location)
		weights = np.array(ROI_weights).flatten()
		weighted_voxel_vals = np.multiply(voxel_vals, weights)
		average = np.true_divide(np.sum(weighted_voxel_vals), np.sum(weights))
		average = int(round(float(average)))
		return average
				
	def get_voxel(self, volume, spatial_coords):
		""" Get the value from the voxel specified by coordinates """
		return volume[spatial_coords[0]][spatial_coords[1]][spatial_coords[2]]			# remember spatial_coords order should be X,Y,Z
		
	def write_log(self, text_to_write, log_name):
		""" Open log file, write the specified text to it, close """
		log_message = (time.asctime() + ' ----- ' + text_to_write + '\n' )
		log_file = open(log_name, 'a')
		log_file.write(log_message)
		log_file.close()
		
	

