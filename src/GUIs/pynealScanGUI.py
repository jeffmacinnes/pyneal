#!/usr/bin/env python
# encoding: utf-8
"""
PynealScanGUI.py

GUI for setting up parameters for real-time analysis
-jjm 7/2016
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
from tkFileDialog import asksaveasfilename
from tkMessageBox import *


class PynealScanGUI:
	""" A class to pop up a GUI to collect user input settings
		prior to beginning real-time analysis
	"""
	
	def __init__(self, pynealDir):							# initialize GUI and default variables
		# initialize main GUI
		self.root = Tk()
		self.root.title('Pyneal')
		self.create_menubar()
		self.main_frame = Frame(self.root)
		self.main_frame.pack()
		
		# initialize variables, set to default values
		self.pyneal_dir = pynealDir									# will store the path of the root pyneal folder
		self.DATA_dir = os.path.join(self.pyneal_dir, 'data')
		self.submitted = False										# will change to TRUE once the "submit button is pressed"
		self.hdr_color = '#ca3e52'									# variable to control the hdr color
		self.bg_color = '#ffffff'									# variable to control the bg color
		self.ROI_instances = {}
 
		self.host = StringVar()										# variable for specifying the host ip address
		self.in_port = StringVar()									# variable for the incoming TCP/IP port
		self.out_port = StringVar()									# variable for the outgoing TCP/IP port
		self.n_tmpts = StringVar()									# variable for the number of timepts
		self.preproc_choice = IntVar()								# variable for the preprocessing choice, raw or incGLM
		self.current_design = StringVar()							# variable for a label that will display the name of design file
		self.mean_regressor_choice = IntVar()						# variable for whether to include a mean regressor in the incGLM design
		self.motion_regressors_choice = IntVar()					# variable for whether to calculate motion paramters for incGLM design
		self.roi_choice = IntVar()									# variable for choice of ROI type, mask or defined
		self.current_mask = StringVar()								# variable for a label to display the name of mask file
		self.mask_dimensions = StringVar()							# variable to display the dimensions of the selected mask
		self.mask_wt_choice = IntVar()								# variable to store mask weighting choice
		self.mask_n_nonzero_vox = StringVar()						# variable to display the number of nonzero voxels in selected mask
		self.n_ROIs = StringVar()									# variable for the number of ROIs
		self.roi_cx = StringVar()									# variable for the center X coordinate for sphere ROI
		self.roi_cy = StringVar()									# variable for the center Y coordinate for sphere ROI
		self.roi_cz = StringVar()									# variable for the center Z coordinate for sphere ROI
		self.roi_rad = StringVar()									# variable for the radius for sphere ROI
		self.stat_choice = IntVar()									# variable for the choice of stats to run, average, median, or custom
		self.current_custom_stat_script = StringVar()				# variable for a label to display the name of a custom stat script
		self.log_choice = IntVar()									# variable for whether or not to write the log
		self.save_choice = IntVar()		 							# variable for whether or not to save the stat output data
		self.plot_choice = IntVar()									# variable for whether or not to plot the stat output data as it is calculated

		# load last-used settings (if none, revert to default)	
		if os.path.isfile(os.path.join(self.DATA_dir, 'default_settings.pkl')):				# load saved settings if they exist
			self.populate_GUI_settings(os.path.join(self.DATA_dir,'default_settings.pkl'))
		
		# Defaults (if no saved settings file):
		else:	
			self.host.set("127.0.0.1")									# default host number
			self.in_port.set("50007")									# default incoming port number
			self.out_port.set("50008")									# default outgoing port number
			self.n_tmpts.set("416")										# number of tmpts/run
			self.preproc_choice.set(1)
			self.current_design.set("none")
			self.loaded_design = []										# variable to store a loaded design matrix
			self.design_matrix = []
			self.mean_regressor_choice.set(1)							# default 'add mean regressor' choice (1 for yes, 0 for no)
			self.motion_regressors_choice.set(1)						# default 'add motion regressors' choice (1 for yes, 0 for no)
			self.roi_choice.set(2)
			self.current_mask.set("none")
			self.mask_dimensions.set(" ")
			self.mask_n_nonzero_vox.set(" ")
			self.mask_wt_choice.set(0)
			self.mask = []
			self.n_ROIs.set("1")
			self.roi_cx.set("32")
			self.roi_cy.set("32")
			self.roi_cz.set("16")
			self.roi_rad.set("5")
			self.coordinates = []
			self.weights = []
			self.stat_choice.set(1)
			self.current_custom_stat_script.set("none")
			self.loaded_custom_stat_script = []							# variable to store a loaded custom script
			self.log_choice.set(1)
			self.save_choice.set(1)
			self.plot_choice.set(1)										# default choice to plot output (1) or not (0)										
			
		# create subframes
		self.create_menubar()
		self.create_logo()
		self.create_socket()
		self.create_preproc()
		self.create_roi_settings()
		if self.roi_choice.get()  == 1:
			self.create_mask_roi_window()
		elif self.roi_choice.get() == 2:
			self.create_define_roi_window()
		self.create_stats()
		if self.stat_choice.get() == 3:
			self.create_custom_stat_window()
		self.create_misc()
		self.create_command()			
	
		# Run GUI
		self.root.mainloop()
	
	######### GUI COMPONENTS DEFINITIONS ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ 
	### MENU BAR
	def create_menubar(self):
		self.menubar = Menu(self.root)
		
		# file menu
		self.filemenu = Menu(self.menubar, tearoff=0)
		self.filemenu.add_command(label="Save Settings", command=self.filemenu_save)
		self.filemenu.add_command(label="Load Settings", command=self.filemenu_load)
		self.filemenu.add_separator()
		self.filemenu.add_command(label="Exit", command=self.root.quit)
		self.menubar.add_cascade(label="File", menu=self.filemenu)
		
		self.root.config(menu=self.menubar)	
	
	def filemenu_save(self):
		"""
		upon choosing the 'save' option from the file menu, gather all the settings and 
		prompt the user to choose a new filename for the saved settings
		"""
		self.get_all_values()
		self.save_settings(overwriteDefaults=0)

	def filemenu_load(self):
		"""
		upon choosing the 'load' option from the file menu, prompt user to 
		choose a settings file from a dialog window. Then open that file and populate the GUI 
		with those settings
		"""
		self.settings_file = askopenfilename(defaultextension='.pkl', 
			initialdir=os.path.expanduser('~'),
			title='Select pyneal settings file')
		self.populate_GUI_settings(self.settings_file)
		
	
	### LOGO BOX ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
	def create_logo(self):					# create logo box
		self.logo_frame = Frame(self.main_frame,
			width=300,
			height=92,
			bd=2,
			relief=SUNKEN)
		self.logo_dir = os.path.join(self.pyneal_dir, 'docs/images')
		self.img = PhotoImage(file=os.path.join(self.logo_dir, 'pyneal_logo_small.gif'))
		self.logo_label = Label(self.logo_frame,
			image=self.img).pack(side=TOP)
		self.logo_frame.pack(side=TOP, fill=X, expand=YES)
	
	### SOCKET SETTINGS BOX ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
	def create_socket(self):				# build socket settings box
		# Main socket connctions box frame
		self.socket_frame = Frame(self.main_frame, 
			width=300, 
			height=200, 
			bd=2,
			bg=self.bg_color, 
			relief=SUNKEN)
		self.socket_title = Label(self.socket_frame, 
			text="SOCKET CONNECTION SETTINGS:",
			bg=self.hdr_color,
			font=('helvetica', 12, 'italic')).pack(side=TOP, expand=YES, fill=X)
		
		# Make the Host label
		self.host_label_frame = LabelFrame(self.socket_frame,
			width=300, 
			text=" host IP: ",
			font=('helvetica', 12, 'italic'),
			bg=self.bg_color)
		self.host_label_frame.pack(side=TOP, pady=3, padx=3)

		# set host ip subframe
		self.host_frame = Frame(self.host_label_frame,
			width=300,
			bg=self.bg_color)
		self.host_label = Label(self.host_frame,
			width=20,
			text="Host IP:",
			bg=self.bg_color).pack(side=LEFT)
		self.host_entry = Entry (self.host_frame,
			width=20,
			bg=self.bg_color,
			textvariable=self.host)
		self.host_entry.pack(side=RIGHT, padx=3)
		self.host_frame.pack(side=TOP)

		# Make the port #'s label
		self.ports_frame = LabelFrame(self.socket_frame,
		  	width=300,
			text=" port #'s: ",
			font=('helvetica', 12, 'italic'),
			bg=self.bg_color)

		self.ports_frame.pack(side=TOP, pady=3, padx=3)
		
		# Choose incoming Host subframe
		self.in_port_frame = Frame(self.ports_frame, 
			width=300,
			bg=self.bg_color)
		self.in_port_label = Label(self.in_port_frame, 
			width=20,
			text="Incoming:",
			bg=self.bg_color).pack(side=LEFT)
		self.in_port_entry = Entry(self.in_port_frame, 
			width=20,
			bg=self.bg_color,
			textvariable=self.in_port)
		self.in_port_entry.pack(side=RIGHT, padx=3)
		self.in_port_frame.pack(side=TOP)
	
		# Choose incoming Port subframe
		self.out_port_frame = Frame(self.ports_frame, 
			width=300,
			bg=self.bg_color)
		self.out_port_label = Label(self.out_port_frame, 
			width=20,
			text="Outgoing:",
			bg=self.bg_color).pack(side=LEFT)
		self.out_port_entry = Entry(self.out_port_frame, 
			width=20,
			bg=self.bg_color,
			textvariable=self.out_port)
		self.out_port_entry.pack(side=RIGHT, padx=3)
		self.out_port_frame.pack(side=TOP)

		# Pack the Export Frame
		self.socket_frame.pack(side=TOP, fill=X, expand=YES)
			
	### PREPROCESSING SETTINGS BOX ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
	def create_preproc(self):					# build Preprocessing box
		# Main preprocessing box frame
		self.preproc_frame = Frame(self.main_frame, 
			width=300, 
			height=200, 
			bd=2,
			bg=self.bg_color, 
			relief=SUNKEN)
		self.preproc_title = Label(self.preproc_frame, 
			text="PREPROCESSING:",
			bg=self.hdr_color,
			font=('helvetica', 12, 'italic')).pack(side=TOP, expand=YES, fill=X)

		# N_time points subframe
		self.n_tmpts_frame = Frame(self.preproc_frame, 
			width=300,
			bg=self.bg_color)
		self.n_tmpts_label = Label(self.n_tmpts_frame,
			width=20,
			bg=self.bg_color,
			text="# time points/run:").pack(side=LEFT)
		self.n_tmpts_entry = Entry(self.n_tmpts_frame,
			bg=self.bg_color,
			width=10,
			textvariable=self.n_tmpts)
		self.n_tmpts_entry.pack(side=RIGHT)
		self.n_tmpts_frame.pack(side=TOP)
		
		# Preproc Choice subframe
		self.preproc_choice_frame = LabelFrame(self.preproc_frame,
			width=300,
			text="Data: ",
			font=('helvetica', 12, 'italic'),
			bg=self.bg_color)			
		
		self.preproc_choice_frame.pack(side=TOP, expand=YES, fill=X, pady=3, padx=3)
		
		self.preproc_raw_button = Radiobutton(self.preproc_choice_frame,
			text="Raw Values",
			height=1,
			variable=self.preproc_choice,
			value=1,
			bg=self.bg_color,
			command=self.create_raw_window)
		self.preproc_glm_button = Radiobutton(self.preproc_choice_frame,
			text="Incremental GLM",
			height=1,
			variable=self.preproc_choice,
			value=2,
			bg=self.bg_color, 
			command=self.create_incGLM_window)	
		self.preproc_raw_button.pack(side=LEFT, padx=16)
		self.preproc_glm_button.pack(side=LEFT, padx=16)
		
		# Inc GLM settings frame that will display the options for the settings up incremental GLM
		self.glm_settings_frame = Frame(self.preproc_frame,
			width=300,
			bg=self.bg_color)
		self.glm_settings_frame.pack(side=TOP, fill=X, expand=YES)
		
		if self.preproc_choice.get() == 2:
			self.create_incGLM_window()
		# pack parent preproc frame
		self.preproc_frame.pack(side=TOP, fill=X, expand=YES)	
	
	### ROI SETTINGS BOX ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
	def create_roi_settings(self):
		self.roi_settings_frame = Frame(self.main_frame, 
			width=300, 
			bd=2,
			bg=self.bg_color, 
			relief=SUNKEN)
		self.roi_settings_title = Label(self.roi_settings_frame, 
			text="ROIs:",
			bg=self.hdr_color,
			font=('helvetica', 12, 'italic')).pack(side=TOP, expand=YES, fill=X)
		
		# ROI Choice subframe (choose between 'Mask' and 'Define')
		self.roi_choice_frame = Frame(self.roi_settings_frame,
			width=300,
			bg=self.bg_color)
		self.roi_choice_button_mask = Radiobutton(self.roi_choice_frame,
			text="Mask", 
			variable=self.roi_choice,
			value=1,
			height=2,
			indicatoron=0,
			command=self.create_mask_roi_window).pack(side=LEFT, padx=16)
		self.roi_choice_button_define = Radiobutton(self.roi_choice_frame,
			text="Define", 
			variable=self.roi_choice,
			value=2,
			height=2,
			indicatoron=0,
			command=self.create_define_roi_window).pack(side=LEFT, padx=16)
		self.roi_choice_frame.pack(side=TOP)
		
		# ROI content frame that will display the options available for whatever selection is made
		self.roi_content_frame = Frame(self.roi_settings_frame,
			width=300,
			bg=self.bg_color)
		self.roi_content_frame.pack(side=BOTTOM, fill=X, expand=YES)
		
		# pack the parent roi_settings frame
		self.roi_settings_frame.pack(side=TOP, fill=X, expand=YES)

	### STATS SETTINGS BOX ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
	def create_stats(self):					# build stats box
		# Main stats box frame
		self.stats_frame = Frame(self.main_frame, 
			width=300, 
			height=200, 
			bd=2,
			bg=self.bg_color, 
			relief=SUNKEN)
		self.stats_title = Label(self.stats_frame, 
			text="SUMMARY STATS:",
			bg=self.hdr_color,
			font=('helvetica', 12, 'italic')).pack(side=TOP, expand=YES, fill=X)
		# Radio Buttons:
		self.buttons_frame = Frame(self.stats_frame,
			height=20,
			bg=self.bg_color)
		self.average_button = Radiobutton(self.buttons_frame,
			text="avg", 
			variable=self.stat_choice,
			bg=self.bg_color,
			value=1,
			command=self.clear_stat_window).pack(side=LEFT, padx=6)
		self.median_button = Radiobutton(self.buttons_frame,
			text="median",
			variable=self.stat_choice,
			bg=self.bg_color,
			value=2,
			command=self.clear_stat_window).pack(side=LEFT, padx=6)
		self.custom_button = Radiobutton(self.buttons_frame,
			text="Custom",
			variable=self.stat_choice,
			bg=self.bg_color,
			value=3,
			command=self.create_custom_stat_window).pack(side=LEFT, padx=6)
		self.buttons_frame.pack(side=TOP)
		
		# Custom stat script entry frame
		self.custom_stat_frame = Frame(self.stats_frame,
			width=300,
			bg=self.bg_color)
		self.custom_stat_frame.pack(side=TOP, fill=X, expand=YES)
		
		# pack parent stats frame
		self.stats_frame.pack(side=TOP, fill=X, expand=YES)

	### MISC SETTINGS BOX ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
	def create_misc(self):					# build Miscellaneous box
		# Main miscellaneous box frame
		self.misc_frame = Frame(self.main_frame, 
			width=300, 
			height=200, 
			bd=2,
			bg=self.bg_color, 
			relief=SUNKEN)
		self.misc_title = Label(self.misc_frame, 
			text="MISC OPTIONS:",
			bg=self.hdr_color,
			font=('helvetica', 12, 'italic')).pack(side=TOP, expand=YES, fill=X)
		# write log button
		self.misc_log_checkbutton = Checkbutton(self.misc_frame, 
			text='Write Log',
			bg=self.bg_color, 
			variable=self.log_choice).pack(side=LEFT)
		# write output button
		self.save_output_checkbutton = Checkbutton(self.misc_frame, 
			text='Save Output',
			bg=self.bg_color, 
			variable=self.save_choice).pack(side=LEFT)
		# plot data checkbutton
		self.plot_output_checkbutton = Checkbutton(self.misc_frame,
			text='Plot Motion',
			bg=self.bg_color,
			variable=self.plot_choice).pack(side=LEFT)
		# pack parent misc frame
		self.misc_frame.pack(side=TOP, fill=X, expand=YES)

	
	
	### BOTTOM BUTTON BOX ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
	def create_command(self):					# build Executive Command box 
		
		# Main command box frame
		self.command_frame = Frame(self.main_frame, 
			width=300, 
			height=200, 
			bd=2, 
			relief=SUNKEN)
		
		# Submit Button
		self.submit_button = Button(self.command_frame,
			text="Submit",
			command=self.submit).pack(side=LEFT, fill=X, expand=YES)
		
		# Cancel Button
		self.cancel_button = Button(self.command_frame, 
			text="Cancel",
			command=self.quit).pack(side=LEFT, fill=X, expand=YES)
				
		# pack parent command frame
		self.command_frame.pack(side=BOTTOM, fill=X, expand=YES)
	
#-----------------------------------------------------------------------------------------------------------------------------------------------------	
	# BUTTON DEFINITIONS AND ADDITIONAL FUNCTIONS ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
	
	def create_incGLM_window(self):
		"""create the window with options for incGLM settings"""
		# clear out existing incGLM settings window
		self.clear_window(self.glm_settings_frame)
		
		# load design file
		self.design_file_frame = Frame(self.glm_settings_frame,
								bg=self.bg_color,
								width=300)
		self.current_design_label = Label(self.design_file_frame,
								bg=self.bg_color,
								textvariable=self.current_design,
								font=('helvetica', 12, 'italic')).pack(side=LEFT)
		self.load_design_button = Button(self.design_file_frame,
								bg=self.bg_color,
								text="load design", 
								command=self.load_design).pack(side=RIGHT)
		self.design_file_frame.pack(side=TOP, fill=X, expand=YES)
		
		# additional design options
		self.design_options_frame = Frame(self.glm_settings_frame,
								bg=self.bg_color,
								width=300)
		self.add_motion_checkbox = Checkbutton(self.design_options_frame,
								bg=self.bg_color,
								text="Include Motion Params", 
								variable=self.motion_regressors_choice).pack(side=RIGHT, padx=10)
		self.add_mean_checkbox = Checkbutton(self.design_options_frame,
								bg=self.bg_color,
								text="Add Mean",
								variable=self.mean_regressor_choice).pack(side=RIGHT)

		self.design_options_frame.pack(side=TOP, fill=X, expand=YES)
	
	def create_raw_window(self):
		""" create the window with options for raw values as input"""
		# clear out the existing glm_settings frame
		self.clear_window(self.glm_settings_frame)

	def create_mask_roi_window(self):
		"""create the window with options for loading a premade mask as ROI"""
		# clear out existing roi_content_frame
		self.clear_window(self.roi_content_frame)
		
		# mask selection subframe
		self.mask_selection_frame = Frame(self.roi_content_frame,
									bg=self.bg_color,
									width=300)
		self.current_mask_label = Label(self.mask_selection_frame,
									bg=self.bg_color,
									textvariable=self.current_mask).pack(side=LEFT)
		self.load_mask_button = Button(self.mask_selection_frame,
									text="load mask",
									command=self.load_new_mask).pack(side=RIGHT)
		self.mask_selection_frame.pack(side=TOP, fill=X, expand=YES)
		# mask info subframe
		self.mask_info_frame = Frame(self.roi_content_frame, 
								bg=self.bg_color,
								width=300)
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
		self.mask_options_frame = Frame(self.roi_content_frame,
									bg=self.bg_color,
									width=300)
		self.mask_wt_checkbutton = Checkbutton(self.mask_options_frame, 
								text='Allow weighting (do not binarize)',
								bg=self.bg_color, 
								variable=self.mask_wt_choice).pack(side=LEFT)
		self.mask_options_frame.pack(side=TOP, fill=X, expand=YES)
		
		# pack master roi_content frame
		self.roi_content_frame.pack(side=TOP)
	
	def create_define_roi_window(self):
		""" create window with option for defining a spherical ROI"""
		# clear out existing roi_content_frame
		#for self.widget in self.roi_content_frame.pack_slaves():
		#	self.widget.destroy()
		self.clear_window(self.roi_content_frame)
		
		# number of rois subframe
		self.n_rois_frame = Frame(self.roi_content_frame,										
							bg=self.bg_color,
							width=300)
		self.n_rois_label = Label(self.n_rois_frame,
							bg=self.bg_color,
							text="# of ROIs:").pack(side=LEFT)
		self.n_rois_entry = Entry(self.n_rois_frame,
							bg=self.bg_color,
							width=3,
							textvariable=self.n_ROIs)
		self.n_rois_entry.bind('<Return>', self.create_ROIs)
		self.n_rois_entry.pack(side=LEFT, padx=2)
		self.n_rois_frame.pack(side=TOP)
		self.roi_content_frame.pack(side=TOP)

		# subframe to hold ROI instances
		self.rois_frame = Frame(self.roi_content_frame,					# note: this frame gets packed by the create_ROIs command
  							width=300)
		self.rois_frame.pack(side=TOP)
		self.create_ROIs('none')
	
	def clear_stat_window(self):
		""" clear the current contents of the stat window """
		self.clear_window(self.custom_stat_frame)
	
	def create_custom_stat_window(self):
		""" create window with options for loading a custom stat script"""
		# clear out existing custom stat settings window
		self.clear_window(self.custom_stat_frame)
		
		# Top frame (script title, load button)
		self.custom_stat_frame_top = Frame(self.custom_stat_frame,
										bg=self.bg_color,
										width=300)
		self.custom_stat_label = Label(self.custom_stat_frame_top,
								bg=self.bg_color,
								textvariable=self.current_custom_stat_script,
								font=('helvetica', 12, 'italic')).pack(side=LEFT)
		self.load_custom_stat = Button(self.custom_stat_frame_top,
								bg=self.bg_color,
								text="load script", 
								command=self.load_custom_stat_script).pack(side=RIGHT)
		self.custom_stat_frame_top.pack(side=TOP, fill=X, expand=YES)
		
		# Bottom frame (info about custom stat scripts)
		self.custom_stat_frame_bottom = Frame(self.custom_stat_frame,
										bg=self.bg_color,
										width=300)
		self.custom_stat_info = Label(self.custom_stat_frame_bottom,
								bg=self.bg_color,
								text='Note: ROIs specified in a script will trump ROIs specified above',
								font=('helvetica', 11, 'italic')).pack(side=TOP)
		self.custom_stat_frame_bottom.pack(side=TOP, fill=X, expand=YES)
		
		# pack parent custom stat frame
		self.custom_stat_frame.pack(side=TOP)
			
	def load_design(self):
		""" select design file to load. Display the number of regressors"""
		self.loaded_design = askopenfilename(filetypes=[('.txt files', '*.txt'), ('.mat files', '*.mat')])		# design files must be text files
		if self.loaded_design:
			self.current_design.set(str(self.loaded_design).split('/')[-1])				# display the name of the design file
			f,ext = os.path.splitext(self.loaded_design)
			if ext == '.mat':		# fsl-style
				self.design_matrix = self.format_FSL_design(self.loaded_design)
			else:
				self.design_matrix = np.genfromtxt(self.loaded_design)
				self.ppheights = (np.amax(self.design_matrix, axis=0) - np.amin(self.design_matrix, axis=0)) 
			
			# plot the design matrix
			self.plot_design(self.design_matrix)
			
			# make sure n_timepts in design match what the user has specified
			if self.design_matrix.shape[0] != int(self.n_tmpts_entry.get()):
				showwarning('Ok', 'Warning: The number of timepts in the design differs from what is specified')
	
	def format_FSL_design(self, design_file):
		""" will read in an FSL-style .mat design file, and reformat it for pyneal (Note: stolen from PyMVPA ver 1.0)"""
		f = open(design_file, 'r')
		
		# read header info
		for i, line in enumerate(f):
			if line.startswith('/NumWaves'):
				n_waves = int(line.split()[1])
			if line.startswith('/NumPoints'):
				n_timepts = int(line.split()[1])
			if line.startswith('/PPheights'):
				self.ppheights = [float(i) for i in line.split()[1:]]
			if line.startswith('/Matrix'):
				matrix_offset = i + 1
		f.close()
		
		# load in the regressor data from design file
		design_matrix = np.genfromtxt(design_file, skiprows=matrix_offset) 
		return design_matrix
	
	def plot_design(self, design_matrix):
		""" Plot the design matrix to confirm it looks approrpriate (Note: stolen from PyMVPA ver 1.0 code)"""
		# import internally
		import matplotlib.pyplot as plt
		
		# common y-axis
		yax = np.arange(0, design_matrix.shape[0])
		axcenters = []
		col_offset = max(self.ppheights)
		
		# for all columns
		for i in xrange(design_matrix.shape[1]):
			axcenter = i * col_offset
			plt.plot(design_matrix[:,i] + axcenter, yax)
			axcenters.append(axcenter)
		plt.xticks(np.array(axcenters), range(design_matrix.shape[1]))
		
		# labels and turn y-axis upside down
		plt.ylabel('Samples (top to bottom)')
		plt.xlabel('Regressors')
		plt.ylim(design_matrix.shape[0], 0)
		
		# show plot
		plt.show()
		
	def load_new_mask(self):
		""" select a mask to load. Will convert mask to numpy array """
		self.loaded_mask = askopenfilename(filetypes=[('.img files', '*.img')])			# masks must be in .img binary files
		if self.loaded_mask: 													
			self.current_mask.set(str(self.loaded_mask).split('/')[-1])
			self.mask_binary = open(self.loaded_mask).read()							# read in the binary file of the selected mask
			self.mask_datatype = self.get_hdr_info(self.loaded_mask, 'datatype')		# figure out the datatype of the mask image
			self.mask_xdim = self.get_hdr_info(self.loaded_mask, 'dim1')				# grab the x-dimension 
			self.mask_ydim = self.get_hdr_info(self.loaded_mask, 'dim2')				# grab the y-dimension
			self.mask_zdim = self.get_hdr_info(self.loaded_mask, 'dim3')				# grab the z-dimension
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
	
	def load_custom_stat_script(self):
		""" load in a custom (python) stat script """
		self.loaded_custom_stat_script = askopenfilename(initialdir=os.path.join(self.pyneal_dir, 'custom_stats/stat_scripts'), 
														filetypes=[('.py files', '*.py')])			# custom scripts must be .py files
		if self.loaded_custom_stat_script:
			self.current_custom_stat_script.set(str(self.loaded_custom_stat_script).split('/')[-1])
		else:
			self.current_custom_stat_script.set('none')
	
	def get_hdr_info(self, input_vol, value):
		""" retrieve the requested header value from a dataset """
		self.cmd_str = ('fslval ' + input_vol + ' ' + value)				# FSL command to get 'value' from the image hdr. REQUIRES FSL
		self.output = os.popen(self.cmd_str)
		return int(self.output.read()) 
	
	def create_ROIs(self, event):
		""" Command bound to <Return> key, create entry forms for all of the ROIs specified """
		if len(self.ROI_instances)>0:
			for name in self.ROI_instances:
				self.ROI_instances[name].roi_frame.pack_forget()	# first clear any existing entry forms, then:
			self.ROI_instances = {}									# reset the ROI_instances list
		self.n_ROIs_entered = int(self.n_rois_entry.get())			# grab the number of ROI instances to make
		for roi_number in range(self.n_ROIs_entered):				# for each one:
			counter = roi_number + 1							
			name = "ROI_" + str(counter)							# give it a name
			self.create_ROI_instance(name, counter)					# create an instance with that name
		self.rois_frame.pack(side=TOP)
		
	def create_ROI_instance(self, name, counter):
		""" create a uniquely named instance of each ROI """
		self.ROI_instances[name] = ROI_GUI(self.rois_frame, counter, self.roi_cx, self.roi_cy, self.roi_cz, self.roi_rad)		
	
	def clear_window(self, window_frame):
		""" clear out the widgets from the window_frame specified"""
		for self.widget in window_frame.pack_slaves():
			self.widget.pack_forget()
			#self.widget.destroy()
	
	def submit(self):
		"""upon submission, retrieve all values, save a new default settings list, and close the GUI"""
		self.get_all_values()
		self.save_settings(overwriteDefaults=1)
		self.submitted = True
		self.root.destroy()
	
	def populate_GUI_settings(self, settings_file):
		"""
		Open the specified settings file and fill in the GUI 
		with all of the loaded settings
		"""
		self.fname = file((settings_file), 'r')
		(host_settting,
		in_port_setting,
		out_port_setting,
		n_tmpts_setting,
		preproc_choice_setting,
		current_design_setting,
		loaded_design_setting,
		design_matrix_setting,
		mean_regressor_choice_setting,
		motion_regressors_choice_setting,
		roi_choice_setting,
		current_mask_setting,
		mask_dimensions_setting,
		mask_n_nonzero_vox_setting,
		mask_wt_choice_setting, 
		mask_setting,
		n_ROIs_setting,
		roi_cx_setting,
		roi_cy_setting,
		roi_cz_setting, 
		roi_rad_setting,
		coordinates_setting,
		weights_setting,
		stat_choice_setting,
		current_custom_stat_script_setting,
		loaded_custom_stat_script_setting,
		log_choice_setting,
		save_choice_setting,
		plot_choice_setting) = pickle.load(self.fname)							# will load in all saved variables
		self.fname.close()

		self.host.set(host_settting)
		self.in_port.set(in_port_setting)										# default incoming port number
		self.out_port.set(out_port_setting)										# default outgoing port number
		self.n_tmpts.set(n_tmpts_setting)										# number of tmpts/run
		self.preproc_choice.set(preproc_choice_setting)
		self.current_design.set(current_design_setting)
		self.loaded_design = loaded_design_setting								# variable to store a path to design matrix
		self.design_matrix = design_matrix_setting								# variable to store the actual design matrix
		self.mean_regressor_choice.set(mean_regressor_choice_setting)			# default 'add mean regressor' choice (1 for yes, 0 for no)
		self.motion_regressors_choice.set(motion_regressors_choice_setting)		# default 'add motion regressors' choice (1 for yes, 0 for no)
		self.current_mask.set(current_mask_setting)
		self.mask_dimensions.set(mask_dimensions_setting)
		self.mask_n_nonzero_vox.set(mask_n_nonzero_vox_setting)
		self.mask_wt_choice.set(mask_wt_choice_setting)
		self.mask = mask_setting
		self.n_ROIs.set(n_ROIs_setting)
		self.roi_cx.set(roi_cx_setting)
		self.roi_cy.set(roi_cy_setting)
		self.roi_cz.set(roi_cz_setting)
		self.roi_rad.set(roi_rad_setting)
		self.coordinates = coordinates_setting
		self.weights = weights_setting
		self.stat_choice.set(stat_choice_setting)
		self.current_custom_stat_script.set(current_custom_stat_script_setting)
		self.loaded_custom_stat_script = loaded_custom_stat_script_setting
		self.log_choice.set(log_choice_setting)
		self.save_choice.set(save_choice_setting)
		self.plot_choice.set(plot_choice_setting)
		
		
	def get_all_values(self):
		"""update all user variable values with settings from the GUI"""
		self.host_setting = self.host.get()									# get the host name
		self.in_port_setting = self.in_port_entry.get()						# get the incoming port number
		self.out_port_setting = self.out_port_entry.get()  					# get the outgoing port number
		self.n_tmpts_setting = self.n_tmpts_entry.get()  					# get the number of time pts
		self.preproc_choice_setting = self.preproc_choice.get()				# get the preproc choice (1 = Raw values, 2 = IncGLM)
		self.current_design_setting = self.current_design.get()
		self.loaded_design_setting = self.loaded_design
		self.design_matrix_setting = self.design_matrix
		self.motion_regressors_choice_setting = self.motion_regressors_choice.get()
		self.mean_regressor_choice_setting = self.mean_regressor_choice.get()
		self.roi_choice_setting = self.roi_choice.get()
		self.current_mask_setting = self.current_mask.get()
		self.mask_dimensions_setting = self.mask_dimensions.get()
		self.mask_n_nonzero_vox_setting = self.mask_n_nonzero_vox.get()
		self.mask_wt_choice_setting = self.mask_wt_choice.get()
		self.mask_setting = self.mask
		self.n_ROIs_setting = self.n_ROIs.get()
		self.roi_cx_setting = self.roi_cx.get()
		self.roi_cy_setting = self.roi_cy.get()
		self.roi_cz_setting = self.roi_cz.get()
		self.roi_rad_setting = self.roi_rad.get()
		self.coordinates_setting = self.coordinates
		self.weights_setting = self.weights
		self.stat_choice_setting = self.stat_choice.get()							# get the stat-choice (1 = Average, 2 = Median)
		self.current_custom_stat_script_setting = self.current_custom_stat_script.get()
		self.loaded_custom_stat_script_setting = self.loaded_custom_stat_script
		self.log_choice_setting = self.log_choice.get()								# get the choice of whether to write a log or not
		self.save_choice_setting = self.save_choice.get()							# get the choice of whether to save the output or not
		self.plot_choice_setting = self.plot_choice.get()							# get the choice of whether to plot the output or not
		
		# ensure appropriate combinations of options are set, warn if not
		if self.roi_choice.get() == 1:        # (roi_type = mask)
			if hasattr(self, 'mask'):												# check to ensure mask is loaded
				self.coordinates, self.weights = stats.get_mask_coordinates(self.mask, self.mask_wt_choice.get())	# create list of all nonzero coordinates & weightsfrom mask
			else:
				showwarning('Ok', 'No mask loaded')
				return
			#self.mask_name = str(self.loaded_mask)
			self.mask_name = self.current_mask_setting													
		elif self.roi_choice.get() == 2:      # (roi_type = defined)
			self.n_ROIs_entered = int(self.n_rois_entry.get())									# check to see if they've specified any ROIs
			if self.n_ROIs_entered > 1:
				showwarning('Ok', 'Pyneal is currently limited to handle only 1 ROI. Please change')
				return
			elif self.n_ROIs_entered == 1:
				self.roi_values = self.ROI_instances['ROI_1'].get_values()
				self.roi_cx_val = self.roi_values[0]							# X coordinate is the first value read in
				self.roi_cy_val = self.roi_values[1]							# Y coordinate is the 2nd value read in
				self.roi_cz_val = self.roi_values[2]							# Z coordinate is the 3rd value read in
				self.roi_rad_val = self.roi_values[3]							# Radius is the 4th value read in
				self.coordinates, self.weights = stats.get_sphere_coords(self.roi_cx_val, self.roi_cy_val, self.roi_cz_val, self.roi_rad_val)
			else:
				showwarning('Ok', 'You must define at least one ROI')
				return
		if self.preproc_choice.get() == 2 and self.stat_choice.get() == 3:
			showwarning('Ok', 'NOTE: IncGLM will only be computed on voxels specified by the ROI option. If planning to run a custom stat script with multiple ROIs, consider setting the ROI option to "Mask" and loading a full brain mask (in functional space)')

	def save_settings(self, overwriteDefaults=1):
		""" Will save all of the current user-values to a pickle that will be loaded next time """
		if overwriteDefaults == 1:
			self.fname = file(os.path.join(self.DATA_dir,'default_settings.pkl'), 'w')
		else:
			self.fname = file(asksaveasfilename(initialfile='mySettings.pkl',
												initialdir=os.path.expanduser('~'),
												title='Save Settings as....'), 'w')
		self.vars = [self.host_setting,
						self.in_port_setting, 
						self.out_port_setting, 
						self.n_tmpts_setting,
						self.preproc_choice_setting,
						self.current_design_setting,
						self.loaded_design_setting,
						self.design_matrix_setting,
						self.mean_regressor_choice_setting,
						self.motion_regressors_choice_setting,
						self.roi_choice_setting,
						self.current_mask_setting,
						self.mask_dimensions_setting,
						self.mask_n_nonzero_vox_setting,
						self.mask_wt_choice_setting,
						self.mask_setting,
						self.n_ROIs_setting,
						self.roi_cx_setting,
						self.roi_cy_setting,
						self.roi_cz_setting,
						self.roi_rad_setting,
						self.coordinates_setting,
						self.weights_setting,
						self.stat_choice_setting, 
						self.current_custom_stat_script_setting,
						self.loaded_custom_stat_script_setting,
						self.log_choice_setting, 
						self.save_choice_setting, 
						self.plot_choice_setting]
		pickle.dump(self.vars, self.fname)
		self.fname.close()
		
	def quit(self):									# close GUI without submitting user values; exits "main.py" script					
		sys.exit()
	
			
			
#()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()

class ROI_GUI:
	"""A class to create ROI GUI from which data will be read from.
	   GUI will pop up in UserGui, providing options for drawing ROIs
	"""
	def __init__(self, parent, roi_n, cx, cy, cz, radius):					# initialize GUI
		self.bg_color = '#ffffff'
		self.roi_frame=Frame(parent,
						width=300,
						height=20,
						bg=self.bg_color,)
		self.cx = cx
		self.cy = cy
		self.cz = cz
		self.radius = radius
		
		# Label for the ROI
		self.ROI_label = Label(self.roi_frame,
							bg=self.bg_color,
							text="ROI " + str(roi_n)).pack(side=TOP, anchor=NW)
		
		# Center coordinates entry
		self.center_coord_frame = Frame(self.roi_frame,
									height=20,
									bg=self.bg_color)
		self.center_coord_label = Label(self.center_coord_frame,
									width=20,
									bg=self.bg_color,
									text="Center (x,y,z):").pack(side=LEFT)
		self.center_x_entry = Entry(self.center_coord_frame,
		 							bg=self.bg_color,
									width=4,
									textvariable=self.cx)
		self.center_x_entry.pack(side=LEFT, padx=2)
		self.center_y_entry = Entry(self.center_coord_frame, 
								bg=self.bg_color,
								width=4,
								textvariable=self.cy)
		self.center_y_entry.pack(side=LEFT, padx=2)
		self.center_z_entry = Entry(self.center_coord_frame, 
								bg=self.bg_color,
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
									bg=self.bg_color,
									width=4,
									textvariable=self.radius)
		self.sphere_radius_entry.pack(side=LEFT)
		self.sphere_radius_frame.pack(side=TOP, expand=YES, fill=X)
		
		# Pack main ROI frame
		self.roi_frame.pack(side=TOP)
		
	def get_values(self):								# Grab values from ROI selection, will be called from the UserGUI class
		self.cx_entered = int(self.center_x_entry.get())				# get the X coordinate
		self.cy_entered = int(self.center_y_entry.get())				# get the Y coordinate
		self.cz_entered = int(self.center_z_entry.get())				# get the Z coordinate
		self.radius_entered = int(self.sphere_radius_entry.get())		# get the sphere radius
		
		return self.cx_entered, self.cy_entered, self.cz_entered, self.radius_entered

	
