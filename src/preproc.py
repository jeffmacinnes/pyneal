#!/usr/bin/env python
# encoding: utf-8
"""
preproc.py

Created by Jeff on 2012-08-16.

Set of classes and functions for preprocessing the data during a real-time run
"""

import sys
import os
import numpy as np
from incGLM import *

################ PREPROC CLASS ##########################################

class SessionPreproc:
	""" A class to provide methods for running preprocessing steps during a real-time scan """
	
	def __init__(self, preproc_choice, **kwargs):
		"""
		Initialize instance of SessionPreproc class
		inputs:
			preproc_choice - choice of preprocessing options (1 = Raw values, 2 = IncGLM )
		
		additional kwargs:
			coordinates - list of voxel coordinates corresponding to the ROI specified by the main GUI
			design - numpy array representing GLM design matrix
			mean_choice - choice of whether to include a mean regressor in design matrix or not (0 = no, 1 = yes)
			motion_choice - choice of whether to include motion regressors in design matrix or not (0 = no, 1 = yes)
		"""
		self.preproc_choice = preproc_choice
		if self.preproc_choice == 2:
			# initialize parameters for incGLM. required kwargs: coordinates, design, mean_choice, motion_choice
			self.coordinates = kwargs['coordinates']
			self.GLM_design = kwargs['design']
			self.mean_reg_choice = kwargs['mean_choice']
			self.motion_reg_choice = kwargs['motion_choice']
			
			# create instance of incGLM class
			self.inc_glm = incGLM(self.coordinates, self.GLM_design, self.mean_reg_choice, self.motion_reg_choice)
		
		self.motion_file = '/Users/jeff/Desktop/lab_local/development/incGLM_tests/motion_output.txt'
		
		
	def run_preproc(self, volume):
		"""
		General method for running preprocessing.
		Input: 
			volume - a 3D timepoint to run preprocessing stats on
		Output: 
			preproc_volume - same 3D timepoint after preprocessing
		"""
		if self.preproc_choice == 1:
			# RAW values, no preprocessing. Return raw volume
			self.preproc_volume = volume
			return self.preproc_volume
		
		elif self.preproc_choice == 2:
			# update motion parameters if requested
			if self.motion_reg_choice == 1:
				self.volume_CoM = self.calculate_CoM(volume)
				s = str(self.volume_CoM[0]) + '\t' + str(self.volume_CoM[1]) + '\t' + str(self.volume_CoM[2]) + '\n'
				f = open(self.motion_file, 'a')
				f.write(s)
				f.close()
				
				
				self.inc_glm.updateMotionParameters(self.volume_CoM)
			
			# incGLM; update and recompute the GLM for all timepts up to the current volume
			self.preproc_volume = self.inc_glm.updateGLM(volume)
			
			return self.preproc_volume
			
	def calculate_CoM(self, volume):
		"""
		Calculate the center of mass in 3-directions (x,y,z) for the specified volume
		"""
		[rows, cols, stacks] = volume.shape
		
		# create index arrays for each dimension
		x_ind = np.arange(rows)
		y_ind = np.arange(cols)
		z_ind = np.arange(stacks)

		# summing twice to collapse across dimensions.
		# In each case, for the first summation, axis 0 = X; axis 1 = Y; axis 2 = Z
		# thus, to get the sum in the x-dimension:
		#	1) sum across the z-dimension (axis2) first
		# 	2) in the resulting 2d image, sum across the 2nd dimension (axis 1)
		x_sum = volume.sum(axis=2).sum(axis=1)		# sum across Z, then across Y
		y_sum = volume.sum(axis=2).sum(axis=0)		# sum across Z, then across X
		z_sum = volume.sum(axis=1).sum(axis=0)		# sum across Y, then across X

		# create weighted voxel arrays (weighted by intensity)
		wt_x = x_sum * x_ind
		wt_y = y_sum * y_ind
		wt_z = z_sum * z_ind

		# get average weighted voxel intensity in each dimension
		X = np.true_divide(wt_x.sum(), x_sum.sum())
		Y = np.true_divide(wt_y.sum(), y_sum.sum())
		Z = np.true_divide(wt_z.sum(), z_sum.sum())
		
		X = X*3
		Y = Y*3
		Z = Z*3.8

		return np.array([X,Y,Z])
		
		
		
		
		