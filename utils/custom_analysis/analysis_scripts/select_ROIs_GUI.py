#!/usr/bin/env python
# encoding: utf-8
"""
select_ROIs_GUI.py

-jjm 7/25/12

"""

import sys
import os
import time
import struct
import pickle
import stats
import numpy as np
from Tkinter import *
from tkFileDialog import askopenfilename
from tkMessageBox import *

class ROI_selections:
	""" 
	A class to pop up a GUI to collect center coordinates and desired sphere radii for 2 ROIs
	This class will create the topmost parent frame that will contain the GUI information for each
	of the ROIs
	"""

	def __init__(self):			# initialize GUI
		self.root = Tk()
		self.root.title('Select ROIs')
		self.main_frame = Frame(self.root,
							width=320,
							height=300)
		self.main_frame.pack_propagate(0)
		self.main_frame.pack(fill=X, expand=YES)
		
		# initial config variables
		self.bg_color = '#ffffff'
		self.module_dir = os.path.abspath(os.path.dirname(__file__))
		
		# initialize roi 1 options
		self.r1_roi_choice = IntVar()
		self.r1_cx = StringVar()
		self.r1_cy = StringVar()
		self.r1_cz = StringVar()
		self.r1_rad = StringVar()
		self.r1_current_mask = StringVar()
		self.r1_mask_dimensions = StringVar()
		self.r1_mask_wt_choice = IntVar()
		self.r1_mask_n_nonzero_vox = StringVar()
		
		# initialize roi 2 options
		self.r2_roi_choice = IntVar()
		self.r2_cx = StringVar()
		self.r2_cy = StringVar()
		self.r2_cz = StringVar()
		self.r2_rad = StringVar()
		self.r2_current_mask = StringVar()
		self.r2_mask_dimensions = StringVar()
		self.r2_mask_wt_choice = IntVar()
		self.r2_mask_n_nonzero_vox = StringVar()
		
		# check for saved settings. Load if found, otherwise set default values
		if os.path.isfile(os.path.join(self.module_dir, 'select_ROIs_settings.pkl')):		# load saved settings, if any
			self.fname = file(os.path.join(self.module_dir, 'select_ROIs_settings.pkl'), 'r')
			(r1_roi_choice_setting,
			r1_cx_setting,
			r1_cy_setting,
			r1_cz_setting,
			r1_rad_setting,
			r1_current_mask_setting,
			r1_mask_dimensions_setting,
			r1_mask_n_nonzero_vox_setting,
			r1_mask_wt_choice_setting, 
			r1_mask_setting,
			r2_roi_choice_setting,
			r2_cx_setting,
			r2_cy_setting,
			r2_cz_setting,
			r2_rad_setting,
			r2_current_mask_setting,
			r2_mask_dimensions_setting,
			r2_mask_n_nonzero_vox_setting,
			r2_mask_wt_choice_setting, 
			r2_mask_setting,) = pickle.load(self.fname)				# will load in all of the saved variables
			self.fname.close()
			
			self.r1_roi_choice.set(r1_roi_choice_setting)
			self.r1_cx.set(r1_cx_setting)
			self.r1_cy.set(r1_cy_setting)
			self.r1_cz.set(r1_cz_setting)
			self.r1_rad.set(r1_rad_setting)
			self.r1_current_mask.set(r1_current_mask_setting)
			self.r1_mask_dimensions.set(r1_mask_dimensions_setting)
			self.r1_mask_n_nonzero_vox.set(r1_mask_n_nonzero_vox_setting)
			self.r1_mask_wt_choice.set(r1_mask_wt_choice_setting)
			self.r1_mask = r1_mask_setting
			
			self.r2_roi_choice.set(r2_roi_choice_setting)
			self.r2_cx.set(r2_cx_setting)
			self.r2_cy.set(r2_cy_setting)
			self.r2_cz.set(r2_cz_setting)
			self.r2_rad.set(r2_rad_setting)
			self.r2_current_mask.set(r2_current_mask_setting)
			self.r2_mask_dimensions.set(r2_mask_dimensions_setting)
			self.r2_mask_n_nonzero_vox.set(r2_mask_n_nonzero_vox_setting)
			self.r2_mask_wt_choice.set(r2_mask_wt_choice_setting)
			self.r2_mask = r2_mask_setting
		else:
			self.r1_roi_choice.set(2)						# set default ROI choice (1=loaded mask, 2=sphere)
			self.r1_cx.set('32')
			self.r1_cy.set('32')
			self.r1_cz.set('10')
			self.r1_rad.set('5')
			self.r1_current_mask.set('none')
			self.r1_mask_dimensions.set(' ')
			self.r1_mask_n_nonzero_vox.set(' ')
			self.r1_mask_wt_choice.set(0)
			self.r1_mask = []
			self.r1_coordinates = []
			self.r1_weights = []
			
			self.r2_roi_choice.set(1)						# set default ROI choice (1=loaded mask, 2=sphere)
			self.r2_cx.set('32')
			self.r2_cy.set('32')
			self.r2_cz.set('10')
			self.r2_rad.set('5')
			self.r2_current_mask.set('none')
			self.r2_mask_dimensions.set(' ')
			self.r2_mask_n_nonzero_vox.set(' ')
			self.r2_mask_wt_choice.set(0)
			self.r2_mask = []
		
		# create subframes
		self.create_ROIs()
		self.create_command()

		# Run the GUI
		self.root.mainloop()
		
	def create_ROIs(self):
		""" this function will create a seperate instance of the ROIwindow class for each desired ROI """
		# create the frames that will collect all of the user input. Create instance for each ROI window
		self.r1_window = ROIwindow(parent=self.main_frame,
		 							bg_color='#EDEDED',
									roi_index='1', 
									roi_choice=self.r1_roi_choice.get(),
									cx=self.r1_cx,
									cy=self.r1_cy,
									cz=self.r1_cz,
									rad=self.r1_rad,
									current_mask=self.r1_current_mask,
									mask_dimensions=self.r1_mask_dimensions,
									mask_n_nonzero_vox=self.r1_mask_n_nonzero_vox,
									mask_wt_choice=self.r1_mask_wt_choice,
									mask=self.r1_mask)

		self.r2_window = ROIwindow(parent=self.main_frame,
		 							bg_color="#C7C7C7",
									roi_index='2', 
									roi_choice=self.r2_roi_choice.get(),
									cx=self.r2_cx,
									cy=self.r2_cy,
									cz=self.r2_cz,
									rad=self.r2_rad,
									current_mask=self.r2_current_mask,
									mask_dimensions=self.r2_mask_dimensions,
									mask_n_nonzero_vox=self.r2_mask_n_nonzero_vox,
									mask_wt_choice=self.r2_mask_wt_choice,
									mask=self.r2_mask)
		
		
	def create_command(self):
		""" This function will create the subframe containing the submit and cancel buttons at the bottom of GUI """
		# Main command box frame
		self.command_frame = Frame(self.main_frame, 
								width=300, 
								height=200, 
								bd=2, 
								relief=SUNKEN)
		# Submit Button
		self.submit_button = Button(self.command_frame,
								text="Submit",
								command=self.get_all_values).pack(side=LEFT, fill=X, expand=YES)
		# Cancel Button
		self.cancel_button = Button(self.command_frame, 
								text="Cancel",
								command=self.quit).pack(side=LEFT, fill=X, expand=YES)

		# pack parent command frame
		self.command_frame.pack(side=BOTTOM, fill=X, expand=YES)


# BUTTON DEFINITIONS AND ADDITIONAL FUNCTIONS ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
	# command for 'submit' button
	def get_all_values(self):
		""" upon submission, grab all user variables; save and close GUI """
		
		# r1 variables
		(r1_roi_choice,
		r1_cx,
		r1_cy,
		r1_cz,
		r1_rad,
		r1_current_mask,
		r1_mask_dimensions,
		r1_mask_n_nonzero_vox,
		r1_mask_wt_choice,
		r1_mask) = self.r1_window.get_values()
		
		self.r1_roi_choice_setting = r1_roi_choice
		self.r1_cx_setting = r1_cx
		self.r1_cy_setting = r1_cy
		self.r1_cz_setting = r1_cz
		self.r1_rad_setting = r1_rad
		self.r1_current_mask_setting = r1_current_mask
		self.r1_mask_dimensions_setting = r1_mask_dimensions
		self.r1_mask_n_nonzero_vox_setting = r1_mask_n_nonzero_vox
		self.r1_mask_wt_choice_setting = r1_mask_wt_choice
		self.r1_mask_setting = r1_mask
		
		# r2 variables
		(r2_roi_choice,
		r2_cx,
		r2_cy,
		r2_cz,
		r2_rad,
		r2_current_mask,
		r2_mask_dimensions,
		r2_mask_n_nonzero_vox,
		r2_mask_wt_choice,
		r2_mask) = self.r2_window.get_values()
		
		self.r2_roi_choice_setting = r2_roi_choice
		self.r2_cx_setting = r2_cx
		self.r2_cy_setting = r2_cy
		self.r2_cz_setting = r2_cz
		self.r2_rad_setting = r2_rad
		self.r2_current_mask_setting = r2_current_mask
		self.r2_mask_dimensions_setting = r2_mask_dimensions
		self.r2_mask_n_nonzero_vox_setting = r2_mask_n_nonzero_vox
		self.r2_mask_wt_choice_setting = r2_mask_wt_choice
		self.r2_mask_setting = r2_mask
		
		
		# retrieve coordinates for each roi
		if self.r1_roi_choice_setting == 1:
			self.r1_coords, self.r1_weights = stats.get_mask_coordinates(self.r1_mask_setting, self.r1_mask_wt_choice_setting)
		elif self.r1_roi_choice_setting == 2:
			self.r1_coords, self.r1_weights = stats.get_sphere_coords(int(self.r1_cx_setting), 
																		int(self.r1_cy_setting), 
																		int(self.r1_cz_setting), 
																		int(self.r1_rad_setting))
		if self.r2_roi_choice_setting == 1:
			self.r2_coords, self.r2_weights = stats.get_mask_coordinates(self.r2_mask_setting, self.r2_mask_wt_choice_setting)
		elif self.r2_roi_choice_setting == 2:
			self.r2_coords, self.r2_weights = stats.get_sphere_coords(int(self.r2_cx_setting), 
																		int(self.r2_cy_setting), 
																		int(self.r2_cz_setting), 
																		int(self.r2_rad_setting))
		# save and then quit
		self.save_settings()
		self.root.destroy()
		
	# command for 'quit' button
	def quit(self):
		sys.exit()

	# function to save all of the current GUI settings
	def save_settings(self):
		self.fname = file(os.path.join(self.module_dir, 'select_ROIs_settings.pkl'), 'w')
		self.vars = [self.r1_roi_choice_setting,
					self.r1_cx_setting,
					self.r1_cy_setting,
					self.r1_cz_setting,
					self.r1_rad_setting,
					self.r1_current_mask_setting,
					self.r1_mask_dimensions_setting,
					self.r1_mask_n_nonzero_vox_setting,
					self.r1_mask_wt_choice_setting,
					self.r1_mask_setting,
					self.r2_roi_choice_setting,
					self.r2_cx_setting,
					self.r2_cy_setting,
					self.r2_cz_setting,
					self.r2_rad_setting,
					self.r2_current_mask_setting,
					self.r2_mask_dimensions_setting,
					self.r2_mask_n_nonzero_vox_setting,
					self.r2_mask_wt_choice_setting,
					self.r2_mask_setting]
						
		pickle.dump(self.vars, self.fname)
		self.fname.close()

class ROIwindow:
	" A class to present an instance of an ROI option window "
	def __init__(self, **kwargs):
		# read in keyword arguments
		self.bg_color=kwargs.get('bg_color', "#ffffff")
		self.parent=kwargs['parent']
		self.roi_index=kwargs['roi_index']
		self.roi_choice=IntVar()
		self.roi_choice.set(kwargs['roi_choice'])
		self.cx=kwargs['cx']
		self.cy=kwargs['cy']
		self.cz=kwargs['cz']
		self.rad=kwargs['rad']
		self.current_mask=kwargs['current_mask']
		self.mask_dimensions=kwargs['mask_dimensions']
		self.mask_n_nonzero_vox=kwargs['mask_n_nonzero_vox']
		self.mask_wt_choice=kwargs['mask_wt_choice']
		self.mask=kwargs['mask']
		
		
		# create the frames that will collect all of the user input
		self.ROI_frame = LabelFrame(self.parent,
							width=600,
							height=200,
							bg=self.bg_color,
							text=('ROI ' + self.roi_index +': '),
							font=('helvetica', 14, 'italic'))
		self.roi_choice_frame = Frame(self.ROI_frame,
							width=600,
							bg=self.bg_color)
		self.roi_choice_button_mask = Radiobutton(self.roi_choice_frame,
							text="Mask", 
							variable=self.roi_choice,
							value=1,
							height=2,
							bg=self.bg_color,
							command=self.create_mask_roi_window).pack(side=LEFT, padx=16)
		self.roi_choice_button_define = Radiobutton(self.roi_choice_frame,
							text="Define", 
							variable=self.roi_choice,
							value=2,
							height=2,
							bg=self.bg_color,
							command=self.create_sphere_roi_window).pack(side=LEFT, padx=16)
										
		# ROI content frame that will display the options available for whatever selection is made
		self.roi_content_frame = Frame(self.ROI_frame,
									bg=self.bg_color,
									width=600)
		self.roi_content_frame.pack(side=BOTTOM, fill=X, expand=YES)
		
		# pack enclosing frames
		self.roi_choice_frame.pack(side=TOP, fill=X, expand=YES)			
		self.ROI_frame.pack(side=TOP, fill=BOTH, expand=YES)
		
		if self.roi_choice.get() == 1:
			self.create_mask_roi_window()
		elif self.roi_choice.get() == 2:
			self.create_sphere_roi_window()
		
	def create_mask_roi_window(self):
		""" This function will create an instance of the loadROI class with options for loading a prebuilt mask """
		# clear out the existing contents of the ROI content frame
		self.clear_window(self.roi_content_frame)
		
		# create an instance of the loadROI class
		self.load_window = loadROI(parent=self.roi_content_frame, 
								current_mask=self.current_mask,
								mask_dimensions=self.mask_dimensions,
								mask_n_nonzero_vox=self.mask_n_nonzero_vox,
								mask_wt_choice=self.mask_wt_choice,
								mask=self.mask,
								bg_color=self.bg_color)

	def create_sphere_roi_window(self):
		""" This function will create an instance of the sphereROI class with options for defining a spherical ROI """
		# clear out the existing contents of the ROI content frame
		self.clear_window(self.roi_content_frame)
		
		# create an instance of the sphereROI class
		self.sphere_window = sphereROI(parent=self.roi_content_frame,
									cx=self.cx,
									cy=self.cy,
									cz=self.cz,
									rad=self.rad,
									bg_color=self.bg_color)

	def clear_window(self, window_frame):
		""" clear out the widgets from the window_frame specified """
		for self.widget in window_frame.pack_slaves():
			self.widget.pack_forget()
	
	def get_values(self):
		""" get all of the updated variables from whichever class instance is selected (sphere or loaded ROI) """
		if self.roi_choice.get() == 1:
			self.cx = self.cx.get()
			self.cy = self.cy.get()
			self.cz = self.cz.get()
			self.rad = self.rad.get()
			(self.current_mask, self.mask_dimensions, self.mask_n_nonzero_vox, self.mask_wt_choice, self.mask) = self.load_window.get_values()
		elif self.roi_choice.get() == 2:
			(self.cx, self.cy, self.cz, self.rad) = self.sphere_window.get_values()
			self.current_mask = self.current_mask.get()
			self.mask_dimensions = self.mask_dimensions.get()
			self.mask_n_nonzero_vox = self.mask_n_nonzero_vox.get()
			self.mask_wt_choice = self.mask_wt_choice.get()
				
		self.roi_choice = self.roi_choice.get()
		
		return self.roi_choice, self.cx, self.cy, self.cz, self.rad, self.current_mask, self.mask_dimensions, self.mask_n_nonzero_vox, self.mask_wt_choice, self.mask


class sphereROI:
	" A class to create GUI options for a sphere-based ROI"
	def __init__(self, **kwargs):					# initialize GUI
	 	self.bg_color=kwargs.get('bg_color', "#ffffff")
		self.parent = kwargs['parent']
		self.cx=kwargs['cx']
		self.cy=kwargs['cy']
		self.cz=kwargs['cz']
		self.rad=kwargs['rad']
		
		# Create main sphere options frame
		self.roi_frame=Frame(self.parent,
						width=600,
						height=20,
						bg=self.bg_color)

		
		# Center coordinates entry
		self.center_coord_frame = Frame(self.roi_frame,
									height=20,
									bg=self.bg_color)
		self.center_coord_label = Label(self.center_coord_frame,
									width=20,
									bg=self.bg_color,
									text="Center (x,y,z):").pack(side=LEFT)
		self.center_x_entry = Entry(self.center_coord_frame,
		 							bg='#ffffff',
									width=4,
									textvariable=self.cx)
		self.center_x_entry.pack(side=LEFT, padx=2)
		self.center_y_entry = Entry(self.center_coord_frame, 
								bg='#ffffff',
								width=4,
								textvariable=self.cy)
		self.center_y_entry.pack(side=LEFT, padx=2)
		self.center_z_entry = Entry(self.center_coord_frame, 
								bg='#ffffff',
								width=4,
								textvariable=self.cz)
		self.center_z_entry.pack(side=LEFT, padx=2)
		
		self.center_coord_frame.pack(side=TOP)
		
		# Sphere Radius
		self.sphere_radius_frame = Frame(self.roi_frame,
									bg=self.bg_color,
									height=20)
		self.sphere_radius_label = Label(self.sphere_radius_frame,
									width=20,
									bg=self.bg_color,
									text="Sphere radius (mm):").pack(side=LEFT)
		self.sphere_radius_entry = Entry(self.sphere_radius_frame, 
									bg='#ffffff',
									width=4,
									textvariable=self.rad)
		self.sphere_radius_entry.pack(side=LEFT)
		self.sphere_radius_frame.pack(side=TOP, expand=YES, fill=X)
		
		# Pack main ROI frame
		self.roi_frame.pack(side=TOP, expand=YES, fill=X)
		
	def get_values(self):								# Grab values from ROI selection
		self.cx_entered = int(self.center_x_entry.get())				# get the X coordinate
		self.cy_entered = int(self.center_y_entry.get())				# get the Y coordinate
		self.cz_entered = int(self.center_z_entry.get())				# get the Z coordinate
		self.radius_entered = int(self.sphere_radius_entry.get())		# get the sphere radius
		
		return self.cx_entered, self.cy_entered, self.cz_entered, self.radius_entered
		
class loadROI:
	""" A class to create GUI options for loading a premade mask """
	
	def __init__(self, **kwargs):	
		self.bg_color = kwargs.get('bg_color', "#ffffff")
		self.parent = kwargs['parent']		
		self.current_mask=kwargs['current_mask']
		self.mask_dimensions=kwargs['mask_dimensions']
		self.mask_n_nonzero_vox=kwargs['mask_n_nonzero_vox']
		self.mask_wt_choice=kwargs['mask_wt_choice']
		self.mask=kwargs['mask']
		
		# create the main load roi options frame
		self.roi_frame=Frame(self.parent,
						width=600,
						height=20,
						bg=self.bg_color)
		
		# mask selection subframe
		self.mask_selection_frame = Frame(self.roi_frame,
									bg=self.bg_color,
									width=600)
		self.current_mask_label = Label(self.mask_selection_frame,
									bg=self.bg_color,
									textvariable=self.current_mask).pack(side=LEFT)
		self.load_mask_button = Button(self.mask_selection_frame,
									text="load mask",
									bg=self.bg_color,
									command=self.load_new_mask).pack(side=RIGHT)
		self.mask_selection_frame.pack(side=TOP, fill=X, expand=YES)
		
		# mask info subframe
		self.mask_info_frame = Frame(self.roi_frame, 
								bg=self.bg_color,
								width=600)
		self.mask_dimensions_label = Label(self.mask_info_frame, 
										bg=self.bg_color,
										textvariable=self.mask_dimensions,
										font=('helvetica', 12, 'italic')).pack(side=LEFT)
		self.mask_n_nonzero_label = Label(self.mask_info_frame,
										bg=self.bg_color,
										textvariable=self.mask_n_nonzero_vox,
										font=('helvetica', 12, 'italic')).pack(side=LEFT)
		self.mask_info_frame.pack(side=TOP, fill=X, expand=YES)

		# mask options panel subframe
		self.mask_options_frame = Frame(self.roi_frame,
									bg=self.bg_color,
									width=600)
		self.mask_wt_checkbutton = Checkbutton(self.mask_options_frame, 
									text='Allow weighting (do not binarize)',
									bg=self.bg_color, 
									variable=self.mask_wt_choice).pack(side=LEFT)
		self.mask_options_frame.pack(side=TOP, fill=X, expand=YES)

		# pack master roi frame
		self.roi_frame.pack(side=TOP, fill=X, expand=YES)
	
	def load_new_mask(self):
		""" select a mask to load. Will convert mask to numpy array """
		self.loaded_mask = askopenfilename(filetypes=[('.img files', '*.img')])			# masks must be in .img binary files
		if self.loaded_mask: 													
			self.current_mask.set(str(self.loaded_mask).split('/')[-1])
			self.mask_binary = open(self.loaded_mask).read()							# read in the binary file of the selected mask
			self.mask_datatype = self.get_hdr_info(self.loaded_mask, 'datatype')				# figure out the datatype of the mask image
			self.mask_xdim = self.get_hdr_info(self.loaded_mask, 'dim1')						# grab the x-dimension 
			self.mask_ydim = self.get_hdr_info(self.loaded_mask, 'dim2')						# grab the y-dimension
			self.mask_zdim = self.get_hdr_info(self.loaded_mask, 'dim3')						# grab the z-dimension
			if self.mask_datatype == 16:
				self.mask_unpacked = struct.unpack((str(len(self.mask_binary)/4) + 'f'), self.mask_binary)		# unpack the binary data according to dtype
			else:
				print 'ERROR: pyneal currently only handles masks of float (32bit) datatype. Float is the FSL default.'
				print 'Change the datatype of the mask. Or, tell jeff to fix the code'
			self.mask_array = np.array(self.mask_unpacked)														# convert to np array
			self.mask_array = np.reshape(self.mask_array, (self.mask_zdim, self.mask_ydim, self.mask_xdim))		# reshape array according to image dims
			self.mask_array = self.mask_array.T																	# transpose the mask to [x, y, z]
			self.mask_dimensions.set(str(self.mask_array.shape))												# update the GUI
			self.mask_n_nonzero_vox.set(str(len(np.nonzero(self.mask_array)[0])) + ' voxels')					# update the GUI
			self.mask = self.mask_array
			
	def get_hdr_info(self, input_vol, value):
		""" retrieve the requested header value from a dataset """
		self.cmd_str = ('fslval ' + input_vol + ' ' + value)				# FSL command to get 'value' from the image hdr. REQUIRES FSL
		self.output = os.popen(self.cmd_str)
		return int(self.output.read())
				
	def get_values(self):								# Grab values from ROI selection
		self.current_mask= self.current_mask.get()
		self.mask_dimensions = self.mask_dimensions.get()
		self.mask_n_nonzero_vox= self.mask_n_nonzero_vox.get()
		self.mask_wt_choice= self.mask_wt_choice.get()
		self.mask = self.mask
		
		return self.current_mask, self.mask_dimensions, self.mask_n_nonzero_vox, self.mask_wt_choice, self.mask
		