#!/usr/bin/env python
# encoding: utf-8
"""
stats.py

Created by Jeff MacInnes on 2010-02-26.

Set of functions for computing statistics on a given ROI
"""
import sys
import os
import math
import numpy as np

############## STAT CLASS ###################################################

class SessionStats:
	""" A class to provide methods for statistical analysis during a real-time scan """
	
	def __init__(self, stat_choice, **kwargs):
		"""
		Initialize instance of SessionStats class
		inputs:
			stat_choice - choice of statistical measure to run on the volume (1=average, 2=medium, 3=custom stat script)
		
		additional kwargs:
			coordinates - the list of coordinates (in [X,Y,Z] form) of an ROI to compute the stats within
			weights - list of voxel weights. All set at '1' unless otherwise specified
			stat_script - full path to a custom stat script
		"""
		self.stat_choice = stat_choice
		if self.stat_choice == 1:
			# calculate mean. required kwargs: coordinates, weights
			self.coordinates = kwargs['coordinates']
			self.weights = kwargs['weights']
		elif self.stat_choice == 2:
			# calculate median. required kwargs: coordinates
			self.coordinates = kwargs['coordinates']
		elif self.stat_choice == 3:
			# use custom stat script. required kwards: stat_script (full path to stat script)
			self.stat_script = kwargs['stat_script']
			self.coordinates = kwargs['coordinates']
			
			# import the specified custom stat module
			self.module_path, self.module_name = os.path.split(self.stat_script)
			self.module = self.module_name.split('.')[0]
			sys.path.append(self.module_path)
			self.custom_stat_module = __import__(self.module)
			
			# create instance of custom stat class
			self.custom_stat_class = self.custom_stat_module.CustomStatClass(self.coordinates)
		
		
	def run_stats(self, volume):
		"""
		General method for running stats
		Inputs:
			volume - a 3D timepoint to run stats on
		Outputs:
			stat_output - the output of the selected stat measurement
		"""
		if self.stat_choice == 1:
			self.stat_output = self.get_average(volume)
		elif self.stat_choice == 2:
			self.stat_output = self.get_median(volume)
		elif self.stat_choice == 3:
			self.stat_output = self.run_custom_stat(volume)	
		return self.stat_output
	
	def get_average(self, volume):
		""" Return the weighted average from the ROI specified by self.coordinates from the specified 3d volume """
		voxel_vals = []
		for vox_location in self.coordinates:
			#print volume.shape
			value = self.get_voxel(volume, vox_location)
			voxel_vals.append(value)
		voxel_vals = np.array(voxel_vals)
		weights = np.array(self.weights).flatten()
		weighted_voxel_vals = np.multiply(voxel_vals, weights)
		average = np.true_divide(np.sum(weighted_voxel_vals), np.sum(weights))	
		average = int(round(float(average)))
		return average
		
	def get_median(self, volume):
		""" Return the median value from the ROI specified by self.coordinates from the specified 3d volume """
		voxel_vals = []
		for vox_location in self.coordinates:
			value = self.get_voxel(volume, vox_location)
			voxel_vals.append(value)
		median = np.median(voxel_vals)
		median = int(round(float(median)))
		return median
	
	def run_custom_stat(self, volume):
		""" Return the output of a custom stat script executed on the specified 3d volume """
		stat_output = self.custom_stat_class.compute_stats(volume)
		return stat_output
	
	# additional class utilities ##########################################	
	def get_voxel(self, volume, spatial_coords):
		""" Get the raw value of the voxel at the specified spatial coordinates """
		return volume[spatial_coords[0]][spatial_coords[1]][spatial_coords[2]]			# remember spatial_coords order should be X,Y,Z
	
	
############## ADDITIONAL TOOLS/METHODS ###################################################
	
def get_sphere_coords(cx, cy, cz, rad):
	""" Return the sphere coordinates of a specified radius around a specified center point """
	print 'WARNING: Sphere calculation assumes 3.8 isomorphic voxels '
	vox_dims = 3.8 #(mm)											# hard-coded voxel dimension. This assumes isomorphorphic voxels
																	# CHANGE THIS LATER TO BE MORE DYNAMIC
	rx = int(round(float(rad)/vox_dims)) 							# divide the radius (in mm) by the voxel dimensions in each direction 
	ry = int(round(float(rad)/vox_dims)) 							# this will give you a sphere size in voxel dimensions
	rz = int(round(float(rad)/vox_dims)) 	

	cx = int(round(float(cx))) #/vox_dims)) 							# do the same for the center coordinates 
	cy = int(round(float(cy))) #/vox_dims)) 				
	cz = int(round(float(cz))) #/vox_dims)) 
	
	coordinates = []
	weights = []
	# Go through z direction
	for Z in range(int(cz - rz), int(cz + rz + 1)):
		radi =  math.ceil(rz - math.sqrt(rz**2 - (abs(rz - abs(cz - Z)))**2))
		for Y in range(int(cy - radi), int(cy + radi + 1)):
			lx = math.ceil(radi - math.sqrt(radi**2 - (abs(radi - abs(cy - Y)))**2))
			for X in range(int(cx - lx), int(cx + lx + 1)):
				coordinates.append([X, Y, Z])
				weights.append(1.0)				# weight all sphere voxels similarly)
	return (coordinates, weights)				# return the list of all coordinates, weights within the sphere

def get_mask_coordinates(mask, allowWts):
	""" Return a list of all non-zero voxels in a given mask """
	coordinates = []
	weights = []
	nonzero_locations = np.nonzero(mask)
	for i in range(0, len(nonzero_locations[0])):
		coordinates.append([nonzero_locations[0][i], nonzero_locations[1][i], nonzero_locations[2][i],])
		if allowWts == 1:
			weights.append([mask[nonzero_locations[0][i], nonzero_locations[1][i], nonzero_locations[2][i]]])
		else:
			weights.append(1.0)
	print 'sum of weights: ' + str(np.sum(weights))
	return (coordinates, weights)							# return the list of all nonzero coordinates and voxel weights within the mask




	
	