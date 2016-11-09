#!/usr/bin/env python
# encoding: utf-8
"""
custom_template.py

-jjm 07/2016
"""

import sys
import os
import numpy
import time


######### CUSTOM ANALYSIS CLASS


class CustomAnalysis:
	"""
	This is a template file to write custom analysis scripts. 
	Place your custom code within the specified area below. 
	"""
	
	def __init__(self, coordinates):
		""" INSERT CODE TO BE EXECUTED BEFORE RUN BEGINS"""
		# any files in the same directory as your custom analysis script will be added to your path
		self.class_dir = os.path.abspath(os.path.dirname(__file__))
		sys.path.append(self.class_dir)
		###############################################################################	
		############# vvv INSERT USER-SPECIFIED CODE BELOW vvv ########################
		
		# ACCESS TO VOXEL COORDS FROM ROI SPECIFIED BY GUI 
		# (FEEL FREE TO COMMENT OUT IF YOUR SCRIPT DEFINES NEW ROI COORDINATES)
		self.coordinates = coordinates
		
		
		
		############# ^^^ END USER-SPECIFIED CODE ^^^ #################################
		###############################################################################
		
		

	def compute(self, volume):
		""" 
		INSERT CODE TO BE EXECUTED ON EACH VOLUME AS IT ARRIVES
		
		Note: the final output of any calculations must be stored in 
		a variable named 'analysisOutput'
		"""
		
		###############################################################################	
		############# vvv INSERT USER-SPECIFIED CODE BELOW vvv ########################
		
		self.analysisOutput = 1
	
	

		############# ^^^ END USER-SPECIFIED CODE ^^^ #################################
		###############################################################################
		return self.analysisOutput


########################################################################
######## vvv SPECIFY ANY ADDITIONAL METHODS BELOW vvv ##################
