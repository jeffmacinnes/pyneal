#!/usr/bin/env python
"""
motion.py
motion calculations
"""

import os
import sys
import numpy as np
import time

def CenterOfMass(volume):
	"""
	Given a 3-dimensional volume, will calculate
	the Center of Mass in each of the 3-dimensions. 
	Will return numpy array with 3 values:
		- X: center of mass in x-dimension
		- Y: center of mass in y-dimension
		- Z: center of mass in z-dimension
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
	
	# voxel dims
	voxel_dims = np.array([3, 3, 3.8])
	return np.array([X,Y,Z])*voxel_dims

def calculate_motion(input_image, reference):
	motion = CenterOfMass(input_image)
	change = motion - reference
	return change 



	
	
	
