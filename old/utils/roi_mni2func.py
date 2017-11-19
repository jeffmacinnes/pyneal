#!/usr/bin/env python
# encoding: utf-8
"""
roi_mni2func.py

Tool to transform a given ROI from MNI space to subject functional space

//  Created by Jeff MacInnes                                       //
//  Last modified by Shabnam Hakimi (March 2017)                   //
//  Changes made:                                                  //
//  * modified  group ownership of files output by fslchfiletype   //
//    (correcting for issue potentially unique to BIAC computers)  //
//  * imported glob to manage wildcards for os.chown		       //

"""

import sys
import os
import time
import shutil
import numpy as np 
from Tkinter import *
from tkFileDialog import askopenfilename
import glob

### Config Vars
(pyneal_dir, util_dir) = os.path.split(os.path.abspath(os.path.dirname(__file__)))
MNI_dir = os.path.join(pyneal_dir, 'data/MNI_templates')
SRC_dir = os.path.join(pyneal_dir, 'src')

# add dirs to search path
for d in [MNI_dir, SRC_dir]:
	sys.path.append(d)

### IN-SCRIPT FUNCTIONS #### ***************************************************************
class roi_mni2func_GUI:
	""" 
	GUI to select/load info for converting roi from MNI to func space
	"""

	def __init__(self):							# initialize GUI and default variables
		# initialize main GUI
		self.root = Tk()
		self.root.title('mni2func Mask Transform')
		self.main_frame = Frame(self.root)
		self.main_frame.pack()
		
		# initialize variables, set to defaults
		self.pyneal_dir = pyneal_dir
		self.template_dir = MNI_dir															# path to the MNI template brain
		self.mask_dir = os.path.join(self.pyneal_dir, 'data/masks')	 					# path to masks in MNI space
		self.search_dir = self.pyneal_dir													# default path to start the openFile dialog window in
		self.submitted = False																# will change to TRUE once the "submit button is pressed"
		self.current_func = StringVar()														# variable for a label that will display the name of the selected func image
		self.current_func.set("none")
		self.current_anat = StringVar()														# variable for a label that will display the name of the selected anat image
		self.current_anat.set("none")
		self.current_mask = StringVar()														# variable for the currently selected mask
		self.mask_options = []																# variables to store a list of available masks
		for mask in os.listdir(self.mask_dir):												# go through contents of mask_dir
			if mask[-7:] == '.nii.gz':														# only add the .nii.gz files to the list of options
				self.mask_options.append(mask)
		self.current_mask.set(self.mask_options[0])
		self.output_name = StringVar()														# variable to store the desired output name
		self.output_name.set("*no spaces")
		
		# create subframes
		self.create_user_input()															# create the subframe for choosing the subject data
		self.create_mask_select()
		self.create_output_name()
		self.create_command()
		
		# Run the GUI
		self.root.mainloop()

	### Define subframes of GUI
	def create_user_input(self):
		self.info_frame = Frame(self.main_frame)
		self.info_label = Label(self.info_frame,
			foreground='#AAA',
			justify=LEFT,
			pady=20,
			text="Transform ROI from MNI to functional space. Output saved to Func data directory",
			wrap=260).pack(side=TOP, expand=YES, fill=X)
		self.info_frame.pack(side=TOP)

		# make the frame that will contain all of the user input widgets
		self.user_input_frame = LabelFrame(self.main_frame,
									width=600,
									height=200,
									text='Choose Subject Data:',
									font=('helvetica', 12, 'italic'))
		## Load FUNC
		self.func_input_frame = Frame(self.user_input_frame,
									width=300)
		self.func_input_label = Label(self.func_input_frame,
									width=20,
									text="Func data (4D):").pack(side=LEFT)
		self.func_choose_button = Button(self.func_input_frame,
									text="load func",
									command=self.load_func).pack(side=RIGHT)
		self.func_input_frame.pack(side=TOP)
		
		self.current_func_frame = Frame(self.user_input_frame,
									width=300)
		self.current_func_label = Label(self.current_func_frame,
									textvariable=self.current_func).pack(side=LEFT)
		self.current_func_frame.pack(side=TOP)
		
		# Load ANAT
		self.anat_input_frame = Frame(self.user_input_frame,
									width=300)
		self.anat_input_label = Label(self.anat_input_frame,
									width=20,
									text="Anatomical:").pack(side=LEFT)
		self.anat_choose_button = Button(self.anat_input_frame,
									text="load anat",
									command=self.load_anat).pack(side=RIGHT)
		self.anat_input_frame.pack(side=TOP)
		
		self.current_anat_frame = Frame(self.user_input_frame,
									width=300)
		self.current_anat_label = Label(self.current_anat_frame,
									textvariable=self.current_anat).pack(side=LEFT)
		self.current_anat_frame.pack(side=TOP)
		
		# pack the parent user_input frame
		self.user_input_frame.pack(side=TOP, fill=X, expand=YES)
	
	def create_mask_select(self):
		# make the frame that will contain the mask selection options
		self.mask_select_frame = LabelFrame(self.main_frame,
									width=600,
									height=200,
									text='Choose MNI Mask:',
									font=('helvetica', 12, 'italic'))
		# make the mask selection menu
		self.mask_select_meu = apply(OptionMenu, (self.mask_select_frame, self.current_mask) + tuple(self.mask_options)).pack(side=TOP)	
		
		# pack the parent frame
		self.mask_select_frame.pack(side=TOP, fill=X, expand=YES)	
	
	def create_output_name(self):
		# make the frame that will contain the textfield box to write in the desired output name
		self.output_name_frame = LabelFrame(self.main_frame, 
									width=600,
									height=300,
									text='Choose output name:', 
									font=('helvetica', 12, 'italic'))
		# make the text entry box
		self.output_name_textbox = Entry(self.output_name_frame,
									textvariable=self.output_name).pack(side=RIGHT)
		
		# make the label for the text entry box
		self.current_anat_label = Label(self.output_name_frame,
									text="ROI prefix: ").pack(side=RIGHT)
		
		# pack the parent output name frame
		self.output_name_frame.pack(side=TOP, fill=X, expand=YES)
	
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
								command=self.get_all_values).pack(side=LEFT, fill=X, expand=YES)
		# Cancel Button
		self.cancel_button = Button(self.command_frame, 
								text="Cancel",
								command=self.quit).pack(side=LEFT, fill=X, expand=YES)

		# pack parent command frame
		self.command_frame.pack(side=BOTTOM, fill=X, expand=YES)


# BUTTON DEFINITIONS AND ADDITIONAL FUNCTIONS ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~		
	# command for 'load func' button
	def load_func(self):
		self.loaded_func = askopenfilename(filetypes=[('.hdr files', '*.hdr')], initialdir=self.search_dir)
		self.current_func.set(str(self.loaded_func).split('/')[-1])
		self.search_dir = os.path.abspath(os.path.dirname(self.loaded_func))
		
	# command for 'load anat' button
	def load_anat(self):
		self.loaded_anat = askopenfilename(filetypes=[('.hdr files', '*.hdr')], initialdir=self.search_dir)
		self.current_anat.set(str(self.loaded_anat).split('/')[-1])
		self.search_dir = os.path.abspath(os.path.dirname(self.loaded_anat))
	
	# command for 'submit' button
	def get_all_values(self):
		self.func_image = self.loaded_func
		self.anat_image = self.loaded_anat
		self.mask_image = self.mask_dir + '/' + self.current_mask.get()
		self.output_prefix = self.output_name.get()
		self.submitted = True
		self.root.destroy()
		
	# command for 'quit' button
	def quit(self):
		sys.exit()

### In-script Functions *****************************************************************
# Open the log file, write the specified log message, close log file
def write_log(text_to_write, log_name):
	""" Open log file, write the specified text to it, close """
	log_message = (time.asctime() + ' ----- ' + text_to_write + '\n' )
	log_file = open(log_name, 'a')
	log_file.write(log_message)
	log_file.close()


### BEGIN TRANSFORMATIONS *****************************************************************
# load GUI, retrieve values
mask_gui = roi_mni2func_GUI()						# create an instance of the roi_mni2func GUI; returns paths for the relevant images
func = mask_gui.func_image							# retrieve path to func image	
hires = mask_gui.anat_image							# retrieve path to anat image
ROI = mask_gui.mask_image							# retrieve path to mask image
outname = str(mask_gui.output_prefix)				# retrieve output prefix to use
MNI = os.path.join(MNI_dir,'MNI152_T1_1mm_brain.nii.gz')		# path to the MNI template

# create output directory
this_dir, func_name = os.path.split(func)
subj_dir = os.path.join(this_dir, 'ROI_transforms')
if os.path.isdir(subj_dir):
	shutil.rmtree(subj_dir)									# if directory already exists, delete the old one
os.mkdir(subj_dir)
origs_dir = os.path.join(subj_dir, 'originals')
os.mkdir(origs_dir)

# create log file
log_name = os.path.join(subj_dir, 'transforms_log.txt')
write_log(('4D func image: ' + func), log_name)
write_log(('Hi-Res Anat image: ' + hires), log_name)
write_log(('Input ROI: ' + ROI), log_name)
write_log(('Output prefix: ' + outname), log_name)

# get .img names for each of the inputs
func_img = (func[:-4] + '.img')
hires_img = (hires[:-4] + '.img')

# copy the source files to the 'originals' directory
shutil.copyfile(ROI, os.path.join(origs_dir, 'ROI.nii.gz'))				# source ROI image
shutil.copyfile(func, os.path.join(origs_dir, 'func.hdr'))				# source 4D func image
shutil.copyfile(func_img, os.path.join(origs_dir, 'func.img'))			# source 4D func image
shutil.copyfile(hires, os.path.join(origs_dir, 'hi-res_anat.hdr'))		# source hi-res anat image
shutil.copyfile(hires_img, os.path.join(origs_dir, 'hi-res_anat.img'))	# source hi-res anat image
shutil.copyfile(MNI, os.path.join(origs_dir, 'MNI_brain.nii.gz'))		# source MNI brain

# redefine vars based on copied images
ROI = os.path.join(origs_dir, 'ROI.nii.gz')
func = os.path.join(origs_dir, 'func.hdr')
hires = os.path.join(origs_dir, 'hi-res_anat.hdr')
MNI = os.path.join(origs_dir, 'MNI_brain.nii.gz')

# start making transformations
start = time.time()

# average the functional run across time to create an average 3D volume
status_msg = 'creating average functional image.... (1/8)'
cmd_str = ('fslmaths ' + func + ' -Tmean ' + (subj_dir + '/average_func'))
print status_msg
write_log(status_msg, log_name)
write_log(cmd_str, log_name)
os.system(cmd_str)

avg_func = (subj_dir + '/average_func.nii.gz')	# average functional image

# record uid and gid of average_func.nii.gz (SH: March 2017)
gid = os.stat(subj_dir + '/average_func.nii.gz').st_gid
uid = os.stat(subj_dir + '/average_func.nii.gz').st_uid

# run brain extraction on hires
status_msg = 'skull stripping hi-res anatomical....(2/8)'
cmd_str = ('bet ' + hires + ' ' + (subj_dir + '/hires_full_brain') + ' -f 0.35')
print status_msg
write_log(status_msg, log_name)
write_log(cmd_str, log_name)
os.system(cmd_str)

hires_brain = (subj_dir + '/hires_full_brain.nii.gz')

# align MNI to hi-res
status_msg = 'creating mni2hires transformation matrix....(3/8)'
cmd_str = ('flirt -in ' + MNI + ' -ref ' + hires_brain + ' -out ' + (subj_dir + '/MNI_1mm_HIRES') + ' -omat ' + (subj_dir + '/mni2hires.mat') + ' -bins 256 -cost corratio -searchrx -180 180 -searchry -180 180 -searchrz -180 180 -dof 9  -interp trilinear')
print status_msg
write_log(status_msg, log_name)
write_log(cmd_str, log_name)
os.system(cmd_str)

mni2hires = (subj_dir + '/mni2hires.mat')		# transform 1

# align hi-res to functional space
status_msg = 'creating hires2func transformation matrix....(4/8)'
cmd_str = ('flirt -in ' + hires_brain + ' -ref ' + avg_func + ' -out ' + (subj_dir + '/hires_FUNC') + ' -omat ' + (subj_dir + '/hires2func.mat') + ' -bins 256 -cost corratio -searchrx -90 90 -searchry -90 90 -searchrz -90 90 -dof 9  -interp trilinear')
print status_msg
write_log(status_msg, log_name)
write_log(cmd_str, log_name)
os.system(cmd_str)

hires2func = (subj_dir + '/hires2func.mat')		# transform 2

# concatenate transform 1 and 2. Note that the transform after '-concat' is the 2nd transformation!
status_msg = 'concatenating mni2hires & hires2func transformations....(5/8)'
cmd_str = ('convert_xfm -omat ' + (subj_dir + '/mni2func.mat') + ' -concat ' + hires2func + ' ' + mni2hires)
print status_msg
write_log(status_msg, log_name)
write_log(cmd_str, log_name)
os.system(cmd_str)

# apply mni2func transformation to the ROI
status_msg = ('applying mni2func transformation to ' + ROI.split('/')[-1] + '....(6/8)')
cmd_str = ('flirt -in ' + ROI + ' -ref ' + avg_func + ' -out ' + (subj_dir + '/' + outname + '_FUNC_weighted') + ' -applyxfm -init ' + (subj_dir + '/mni2func.mat') + ' -interp trilinear')
print status_msg
write_log(status_msg, log_name)
write_log(cmd_str, log_name)
os.system(cmd_str)

# binarize mask
status_msg = ('creating binarized copy of mni2func ROI....(7/8)')
cmd_str = ('fslmaths ' + (subj_dir + '/' + outname + '_FUNC_weighted.nii.gz') + ' -bin ' + (subj_dir + '/' + outname + '_FUNC_mask'))
print status_msg
write_log(status_msg, log_name)
write_log(cmd_str, log_name)
os.system(cmd_str)

# convert from NIFTI to .hdr/.img pair
status_msg = 'converting ROIs (mask and weighted) from NIFTI to .hdr/.img....(8/8)'
cmd_str = ('fslchfiletype ANALYZE ' + subj_dir + '/' + outname + '_FUNC_mask.nii.gz')				# change MASK filetype
print status_msg
write_log(status_msg, log_name)
write_log(cmd_str, log_name)
os.system(cmd_str)

cmd_str = ('fslchfiletype ANALYZE ' + subj_dir + '/' + outname + '_FUNC_weighted.nii.gz')				# change WEIGHTED filetype
write_log(cmd_str, log_name)
os.system(cmd_str)

# change group membership of .hdr/.img mask functional mask outputs of fslchfiletype (SH: March 2017)
for maskout in glob.glob((subj_dir + '/' + outname + '._FUNC_*')):			
    os.chown(maskout, uid, gid)												# match group membership to average_func.nii.gz


# cleanup workspace
print 'cleaning up unused files'
cmd_str = ('rm ' + subj_dir + '/hires_full_brain.nii.gz')
os.system(cmd_str)
cmd_str = ('rm ' + subj_dir + '/MNI_1mm_HIRES.nii.gz')
os.system(cmd_str)



weighted_ROI = (subj_dir + '/' + outname + '_FUNC_weighted.img')
masked_ROI = (subj_dir + '/' + outname + '_FUNC_mask.img')
print ('NEW WEIGHTED ROI: ' + weighted_ROI)
print ('NEW MASKED ROI: ' + masked_ROI)


# ask to apply the same transformation to a new ROI or not
applyXfm = raw_input('Apply this mni2func transform to another ROI? (y) or (n)')
ROI2_created = False
if applyXfm == 'y':
	ROI2 = askopenfilename(filetypes=[('.hdr files', '*.hdr')], initialdir=this_dir)
	if len(ROI2) > 0:
		ROI2_outname = raw_input('Output prefix: ') 
		status_msg = ('applying mni2func transformation to ' + ROI2.split('/')[-1])	
		print status_msg
		write_log(status_msg, log_name)
		cmd_str = ('flirt -in ' + ROI2 + ' -ref ' + avg_func + ' -out ' + (subj_dir + '/' + ROI2_outname + '_FUNC_weighted') + ' -applyxfm -init ' + (subj_dir + '/mni2func.mat') + ' -interp trilinear')
		write_log(cmd_str, log_name)
		os.system(cmd_str)
		
		# binarize the 2nd ROI
		status_msg = ('creating binarized copy of 2nd ROI..')
		print status_msg
		write_log(status_msg, log_name)
		cmd_str = ('fslmaths ' + (subj_dir + '/' + ROI2_outname + '_FUNC_weighted.nii.gz') + ' -bin ' + (subj_dir + '/' + ROI2_outname + '_FUNC_mask'))
		write_log(cmd_str, log_name)
		os.system(cmd_str)
		
		# convert to ANALYZE format
		status_msg = ('converting 2nd ROI files (mask and weighted) from NIFTI to .hdr/.img')
		write_log(status_msg, log_name)
		for nifti_file in [(ROI2_outname + '_FUNC_weighted.nii.gz'), (ROI2_outname + '_FUNC_mask.nii.gz')]:
			cmd_str = ('fslchfiletype ANALYZE ' + subj_dir + '/' + nifti_file)				# change MASK filetype
			write_log(cmd_str, log_name)
			os.system(cmd_str)
		
		# set paths for fslVIEW
		weighted_ROI2 = (subj_dir + '/' + ROI2_outname + '_FUNC_weighted.img')
		masked_ROI2 = (subj_dir + '/' + ROI2_outname + '_FUNC_mask.img')
		ROI2_created = True

# finish
finish = time.time()
status_msg = ('total time: ' + str(finish-start))
print status_msg
write_log(status_msg, log_name)

# load in FSL view
if ROI2_created:
	cmd_str = ('fslview ' + (subj_dir + '/hires_FUNC.nii.gz') + ' -l GreyScale ' + masked_ROI + ' -l Red ' + weighted_ROI + ' -l Hot ' + masked_ROI2 + ' -l Blue ' + weighted_ROI2 + ' -l Cool')
	os.system(cmd_str)
else:
	cmd_str = ('fslview ' + (subj_dir + '/hires_FUNC.nii.gz') + ' -l GreyScale ' + masked_ROI + ' -l Red ' + weighted_ROI + ' -l Hot')
	os.system(cmd_str)



