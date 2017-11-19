#!/usr/bin/env python
# encoding: utf-8
"""
incGLM.py
-jjm 8/17/2012

Class and methods for calculating GLMs on the fly

2 classes are defined here:
	incGLM: methods specifically adapted for calculating GLMs incrementally
	GLM: generalized group of methods for GLM calculations
"""

import sys
import os
import time
import numpy as np

class incGLM:
	"""
	Class containing methods for computing incremental GLMs
	"""
	def __init__(self, coordinates, design, mean_reg_choice, motion_reg_choice):
		"""
		Initialize instance of incGLM class
		inputs:
			coordinates - list of voxel coordinates from ROI specified within main pyneal GUI. GLM will be computed on these voxels only
			design - full path to design matrix txt file for the GLM. NOTE: First column MUST be the Task Regressor
			mean_choice - choice of whether to include a mean regressor in the design matrix or not (0 = no, 1 = yes)
			motion_choice - choice of whether to compute and include motion parameters in the model (0 = no, 1 = yes)
		"""	
		# initialize class variables
		self.coords = coordinates
		self.design = design
		self.mean_reg_choice = mean_reg_choice
		self.motion_reg_choice = motion_reg_choice
		self.min_n_vols = 20								# specify how many volumes must elapse before beginning to compute GLMs
		self.vol_counter = 0								# initialize a volume counter variable to keep track of how many volumes have arrived
		
		# load and reformat the design matrix
		self.n_timepts = self.design.shape[0]
		if self.mean_reg_choice == 1:
			self.design = np.column_stack((self.design, np.ones(self.n_timepts)))				# add mean regressor to matrix if specified
		if self.motion_reg_choice == 1:
			self.design = np.column_stack((self.design, np.zeros(shape=[self.n_timepts, 3])))	# add empty cols for motion regressors if specified

		# create boolean arrays indicating where specific regressors are located in the design matrix
		self.task_regressor = np.array([i == 0 for i,x in enumerate(np.arange(self.design.shape[1]))])	# True at task column, False elsewhere
		self.nuisance_regressors = np.invert(self.task_regressor)										# False at task column, True elsewhere
		self.all_regressors = np.ones(self.design.shape[1], dtype=bool)									# True at all columns 
		if self.motion_reg_choice == 1:
			self.motion_regressors = np.array([i >= self.design.shape[1]-3 for i,x in enumerate(self.all_regressors)])	# True at last 3 columns, False elsewhere
		
		# preallocate empty matrices to store incoming raw data (n_timepts X n_voxels), and residuals from GLM calculations
		self.raw_data = np.zeros(shape=(self.n_timepts, len(self.coords)))
		self.residuals = np.zeros(shape=((self.n_timepts-(self.min_n_vols-1)), len(self.coords)))
		self.glm_counter = 0								# counter to keep track of how many times the GLM has been run
		self.residuals_mean = np.zeros(len(self.coords))
		self.squared_residuals_sum = np.zeros(len(self.coords))
		
		# tmp SHIT
		self.output = np.zeros(self.n_timepts)
		
	
	def updateGLM(self, volume):
		""" 
		Update the GLM with the supplied volume
		Inputs:. 
			new_volume - 3D matrix of the most recently acquired volume
		Output: 

		"""				
		# increment the volume counter by 1
		self.vol_counter += 1
		
		# If this is the first volume, use it to create the mask
		if self.vol_counter == 1:
			self.mask = self.createMask(volume, self.coords)
			print ('mask sum: ' + str(self.mask.sum()))
			
		# Extract the relevant voxels
		self.masked_volume = self.maskVolume(volume, self.mask)
		
		# append to raw_data array
		self.raw_data[self.vol_counter-1, :] = self.masked_volume
		
		# BEGIN GLM COMPUTATIONS
		# check if there is sufficient data acquired
		if self.vol_counter >= self.min_n_vols:
			
			# increment the GLM counter
			self.glm_counter += 1
			
			# run GLM on the design up to the current timept and the data to calculate Parmeter Estimates			
			self.PEs = self.applyGLM(self.design[:self.vol_counter,:], self.raw_data[:self.vol_counter, :])
			
			# full model estimate (nuisance AND task regressors). Will return *modeled* signal at the current timepoint
			self.full_estimate = self.estimateSignal(self.PEs, self.design[(self.vol_counter-1), :], self.all_regressors)
			
			# calculate residuals for this timepoint, append to the list of residuals at every timept
			self.this_vol_residuals = self.calculateResidual(self.full_estimate, self.raw_data[(self.vol_counter-1), :])			
			self.residuals[(self.vol_counter-self.min_n_vols),:] = self.this_vol_residuals
			
			# calculate the variance in each voxel's residual
			self.model_variance = self.fullModelVariance(self.this_vol_residuals)
			
			# if the GLM has been run at least twice, proceed to calculate variance in full model fit residuals and vox efficiency measures
			if self.vol_counter > self.min_n_vols:
								
				# model the nuisance signal
				self.nuisance_estimate = self.estimateSignal(self.PEs, self.design[(self.vol_counter-1),:], self.nuisance_regressors)
				
				# estimate the activation (i.e. signal due to task and noise, excluding signals from nuisance regressors)
				self.activation_estimate = self.estimateActivation(self.nuisance_estimate, self.raw_data[(self.vol_counter-1),:])
				
				# calculate the voxel efficiency score (activation estimate divided by variance in voxel full model residual)
				self.vox_efficiency = self.voxEfficiencyEstimate(self.activation_estimate, self.model_variance)
			
				# convert any NaN values to 0
				# Note: If there are any dead voxels (i.e. always 0), the vox efficiency measure will contain a NaN. The following code corrects this
				self.vox_efficiency[np.where(np.isnan(self.vox_efficiency))[0]] = 0
					
				# put vox efficiency scores back into 3D volume and return
				self.preproc_volume = np.zeros(shape=self.mask.shape)			# create output volume same size as mask
				self.preproc_volume[self.mask == 1] = self.vox_efficiency		# write the vox_efficiency scores back into preproc vol at the mask locations
				self.preproc_volume = self.preproc_volume.reshape(volume.shape)						# reshape from 1D to 3D
			else:
				# return a volume of all zeros if not enough data yet
				self.preproc_volume = np.zeros(shape=volume.shape)
		else:
			# return a volume of all zeros if not enough data yet
			self.preproc_volume = np.zeros(shape=volume.shape)
		
		# return the preprocessed 3D volume		
		return self.preproc_volume
		
	def updateMotionParameters(self, volume_CoM):
		""" 
		Update the motion parameters with the latest center-of-mass change. 
		Motion parameters are represented as change relative to a reference volume. 
		The reference volume is currently set to be the first volume of the series. 
		input:
			volume_CoM - np array indicating center-of-mass in X,Y,Z directions
		"""
		if self.vol_counter == 0:
			self.motion_reference = volume_CoM				# use the first volume center-of-mass as a reference point
			
		# calculate motion relative to reference (reference is the first volume)
		self.new_motion_params = volume_CoM - self.motion_reference
		
		# append this volume's motion parameters to the design matrix
		self.design[self.vol_counter, self.motion_regressors] = self.new_motion_params
	
	def createMask(self, ref_volume, coordinates):
		""" 
		Given a list of coordinates, create a mask with the same dimensions as the reference volume.
		Inputs:
			ref_volume: a 3D dataset whose dimensions can be used as a reference for the output mask created
			coordinates: a list of [x,y,z] coordinates for the ROI specified by the main user gui. 
		Output:
			mask: flattened 1D array (dtype = boolean) with the same number of elements as the ref_volume. 
		Notes: 
			A mask of the relevant voxels is required before computing the GLM across those voxels. The volume dimensions
			of this mask are unknown until the first volume arrives during the real-time session. Thus, this command
			should be called after the first volume has arrived, but before any GLM computations are carried out.
			
			The output of this function will be a mask that can be used to quickly extract the desired voxels from subsequent volumes 
		"""
		self.coordinates = coordinates
		
		# create mask (all zeros) with dimensions matching the reference volume
		mask = np.zeros(shape=ref_volume.shape)
		
		# set mask values equal to 1 where indicated
		for coord in self.coordinates:
			mask[tuple(coord)] = 1 				# set mask equal to 1 at each coordinate location
		
		# convert to boolean
		mask = np.array(mask == 1)

		# flatten to 1D array. Since the mask is the same shape as the ref_volume, it'll be flattened in the same order
		mask = mask.ravel()
		
		# create a list or 3D coordinates for every place that the flattened mask == 1
		self.mask3Dcoords = [np.unravel_index(x, ref_volume.shape) for x in np.where(mask==1)[0]] 
		
		# return the flattened mask
		return mask
	
	def maskVolume(self, volume, mask):
		"""
		Given a 3D volume, flatten it to 1D and mask it
		inputs:
			volume - a 3D volume
			mask - a 1D boolean array of masked voxels (the length of this array should equal the total number of elements in the input volume)
		output:
			masked_volume - a 1D array of values extracted from the voxels indicated by the mask
		"""
		# flatten the 3D volume to 1D
		volume = volume.ravel()
		
		# extract the values from mask locations only
		masked_volume = volume[mask]
		
		return masked_volume

	def get3Dcoordinate(self, maskedVoxelIndex):
		"""
		Given an index location of a voxel from masked data, return the corresponding 3D coordinates from the full volume
		inputs:
			maskedVoxelIndex - index location from the array of masked voxels. 
		output:
		 	coordinates - numpy array of the X,Y,Z coordinates of the masked voxel specified by the index value
		
		NOTE: 	Remember, masked voxel space is the 1D array (n_voxels) of MASKED voxels only
				Thus, if your mask consists of 3 voxels, the masked voxel array will have a length of 3. This function serves to map
				between index locations in your masked voxel arrays (in this case, possible index locations are 0,1,2) and the 3D coordinates
				that correspond to those voxels in the full 3D volume. 
		"""
		return self.mask3Dcoords[maskedVoxelIndex]
		

	def applyGLM(self, design, data):
		""" 
		Apply GLM instance to the data supplied 
		inputs:
			design - numpy array (n_timepts * n_regressors)
			data - numpy array (n_timepts * n_voxels) 
		output:
			glm_result - numpy array (n_regressors * n_voxels) of the parameter estimates for each regressor, for each voxel 

		Note: Many of the GLM calculations were adapted/stolen from the PyMVPA module, version 1.0
		(The original code can be found in the module mvpa.measures.glm)
		Unfortunately, the GLM functions appear to have been removed from vers2.0 and beyond, so 
		I lifted a stripped down version of them for purposes here.

		Notes on GLM calculation:
		(from http://www.brainvoyager.com/bvqx/doc/UsersGuide/WebHelp/Content/StatisticalAnalysis/The_General_Linear_Model.htm)
		In the case of a single voxel, the GLM can be expressed as y = Xb + e, where:
			y = [n_timepts x 1] vector of raw data
			X = [n_timepts x n_regressors] design matrix
			b = [n_regressor x 1] vector of beta weights (parameter estimates) for each regressor
			e = [n_timepts x 1] vector of residuals at each timept
		By rearranging the equation, you can get: e = y - Xb
		Since we know y and X, the task becomes finding values of b that minimize e. The GLM does this by finding beta values that minimize
		the sum of *squared* error values (squared because error values will be both positive and negative). The optimal values for b can be 
		found with:  b = (X'X)^-1 * X'y, where:
			(X'X) = matrix multiplication of the transposed design matrix and non-transposed design matrix
			           This will give a square matrix where the length of each side equals n_regressors. Each cell contains
			           the scalar product of two regressors. This product is obtained by summing all products of corresponding
			           values from each of the two regressors. This result is also called the variance-covariance matrix. The diagonal
			           represents the variance of a given regressor; cells above and below the diagonal represent covariance between
			           any two regressors. 
			^-1 = The variance-covariance matrix is inverted (denoted by ^-1) before any further computations.
			X'y = evaluates to a [n_regressors x 1] vector, where each element is the scalar product (i.e. covariance) of a 
			           given regressor's timecourse and the observed data timecourse
		"""
		# convert the design matrix to, well, a matrix
		self._design = np.asmatrix(design)

		# transpose design and multiply by self to create the variance-covariance matrix, then invert
		self._inv_VarCovarMat = (self._design.T * self._design).I

		# multiply the inverted inner product by the transposed design
		self._inv_design = self._inv_VarCovarMat * self._design.T

		# get parameter estimates for all voxels at once
		betas = self._inv_design * data

		# convert to array representation
		pe = betas.T.A

		# convert result to (parameter estimates * voxels)
		glm_results = pe.T

		return glm_results
		
	def estimateSignal(self, PEs, regressor_values, included_regressors):
		"""
		Inputs: 
			PEs - dataset with (n_regressors X n_voxels) array of PEs
			regressor_values - (1 X n_regressors) array of regressor values (from original design matrix) at a given timept
			included_regressors - boolean array (1 X n_regressors) with TRUE for every regressor to include
		Output: 
			1d array (n_voxels) of estimated signal at timept for each voxel 

		given a set of PEs (n_regressors X n_voxels), and a corresponding set of regressor values (n_regressors array) from a given timept, 
		calculate the model fit of the dataset. Will return a 1d array of the expected signal contriubtion at each voxel for every
		regressor in the design. For every voxel, each regressor's PE will be multiplied by the 
		regressor value at the specified timept. Within every voxel, the resulting PEs*regressor's will be summed
		across all regressors, producing a 1d array of the estimated signal at each voxel (n_voxels)

		To calculate full model fit, include the full PE dataset (n_regressors X n_voxels) and the full design matrix
		To calculate nuisance model contribution, include just the nuisance PEs (n_nuisanceRegressors X n_voxels) and only the 
		nuisance regressors of the design.

		In any case, the number of rows of the PE dataset must equal the number of columns of the design matrix
		"""
		PEs = PEs[included_regressors,:]						# Extract the included regressors PEs from the dataset object 
		self.regressor_values = regressor_values[:, included_regressors]
		self.signal_components = PEs.T*self.regressor_values				# multiply all PEs by the regressor values. Result (n_voxels X n_included_regressors) 
		self.modeled_signal = np.sum(self.signal_components, axis=1)		# sum across columns (i.e. axis 1)
		return self.modeled_signal

	def calculateResidual(self, estimatedSignal, rawSignal):
		"""
		Inputs: 
			estimatedSignal - (n_voxels X 1) array of estimated signal
			rawSignal - (n_voxels X 1) array of raw signal
		Output: 
			array (n_voxels X 1) of difference between estimate and raw signals

		calculate the residual for each voxel at 1 timept
		"""
		residuals = rawSignal - estimatedSignal					# subtract the estimated signal from the raw signal
		return residuals											# return result		

	def old_fullModelVariance(self, fullModelFitsResiduals):
		"""
		Inputs:
			fullModelFitsResiduals - (n_voxels X n_timepts) array of residuals of each previous incremental model fit
		Output:
			array (n_voxels X 1) of variance in full model fit up to time max(n_timepts)

		calculate the variance in the full model estimation up to the current timept
		"""
		modelVariance = np.std(fullModelFitsResiduals, axis=0)				# calculate the standard deviation columns
		return modelVariance
	
	def fullModelVariance(self, voxelResiduals):
		"""
		Inputs:
			fullModelFitsResiduals - (n_timepts) array of residuals of from current full model fit
		Output:
			array (n_voxels X 1) of variance in full model fit up to time max(n_timepts)

		incrementally calculate the overall variance in each voxel's full model fit residuals with each new timept
		NOTE: this algorithm is much easier computationally than using numpy to calculate the standard deviation. Should speed things up
		"""
		# update the voxelwise squared_sum of residuals up to the current timept
		self.squared_residuals_sum = self.squared_residuals_sum + (voxelResiduals ** 2)
		
		# update the voxelwise mean of the residuals (across time) up to the current timept
		self.residuals_mean = self.residuals_mean + ((voxelResiduals - self.residuals_mean) * np.reciprocal(float(self.glm_counter)))
		
		if self.glm_counter >= 2:
			self.variance = (self.squared_residuals_sum * np.reciprocal(float(self.glm_counter))) - (self.residuals_mean**2)
			
			self.model_fit_stDev = np.sqrt(self.variance)
			return self.model_fit_stDev
		else:
			return None
		
			
	def estimateActivation(self, nuisanceSignal, rawSignal):
		"""
		Inputs:
			nuisanceSignal - (n_voxels X 1) array of estimated nuisance signal at a give timept
			rawSignal - (n_voxels X 1) array of raw signal at a given timept
		Output:
			array (n_voxels X 1) of raw signal excluding any nuisance regressor contribution

		Given that the raw fMRI signal is made up of 3 components (regressors of interest, nuisance regressors, and noise), by
		estimating the nuisance contribution to the overall signal, we can selectively remove it, leaving signal attributable
		to regressors of interest plus noise		
		"""
		self.activationEstimate = rawSignal - nuisanceSignal				# subtract nuisance contribution from the raw signal
		return self.activationEstimate

	def voxEfficiencyEstimate(self, activationEstimate, fullModelVariance):
		"""
		Inputs:
			activationEstimate - (n_voxels X 1) array of the activation estimates at a given timept
			fullModelVariance - (n_voxles X 1) array of variance in the full model fit up to current timept
		Outputs:
			array (n_voxels X 1) of the voxel_efficiency output at a given timept

		Voxel Efficiency calculation. This calculation converts the activation estimate to a z-score
		by dividing by the standard deviation of the noise for each full model fit up to the current timept
		"""
		self.voxel_efficiency = np.true_divide(activationEstimate, fullModelVariance)	# divide the activation estimate by the full model variance	

		return self.voxel_efficiency
	
	def saveDesign(self, fname):
		"""
		Save the design matrix as a tab-delimited txt file
		"""
		print 'design shape:'
		print self.design.shape
		np.savetxt(fname, self.design, delimiter='\t')

		