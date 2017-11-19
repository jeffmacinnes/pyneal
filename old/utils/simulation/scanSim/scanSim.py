#!/usr/bin/env python
# encoding: utf-8
"""
scanSim.py

Created by Jeff MacInnes on 2010-03-05.

usage:
	> scanSim.py 	:default settings
	> scanSim.py -f		:fast mode. No delay between slices 

This simulation mimics the output from fScan to as great a degree as possible. Use this script
to test pyneal software without having to run an actual scan. 

This script will look for a previously loaded 4d image file stored in the local 'data' folder.
If found, it will display the original file name, and ask whether this is the image you would like 
to simulate the scan with. 
If yes, it will send the image over the socket connection slice by slice, preceded each time by the appropriate 
xml header. 

If you'd like to select a different 4d image, select that option and you will be prompted with a dialog window
asking you to select a new image. 

4d compressed Nifti files (.nii.gz) and HDR files (.hdr) are both eligible options. The only caveat
is that the selected image MUST be of 16-bit integer datatype! (You can check this by running 'fslinfo' on
the desired image)

The selected image will then be copied to the local data directory within the scanSim folder. If you have selected
a HDR file, both the .hdr and the corresponding .img file will be copied to the data directory. This image pair 
will be converted to a Nifti image and saved before proceeding.   
"""

import sys
import os
import shutil
from socket import *
import struct
import numpy as np
import pickle
import time
import re
import nibabel as nib
from tkFileDialog import askopenfilename


# Socket Settings
host='127.0.0.1'
port=5557

# Initial Setup
v = 1
z = 1
data_dir = os.path.join(os.path.abspath(os.path.dirname(sys.argv[0])), 'data')			# will return the path that pyneal lives in


if os.path.isfile(os.path.join(data_dir, 'saved_nifti_volume.pkl')):
	# load data if there is any saved
	fname = file(os.path.join(data_dir, 'saved_nifti_volume.pkl'))
	(scan_images,
	input_path,
	n_slices,
	TR) = pickle.load(fname)
	fname.close()
	
	# ask to load new data if necessary
	print ('Current file: ' + input_path)
	useCurrentDataset = raw_input('Use this dataset? (y/n)')
else:
	useCurrentDataset = 'n'

if useCurrentDataset == 'n':
	print 'Select the 4d functional image (.nii.gz or .hdr)....'
	input_path = askopenfilename(filetypes=[], initialdir='/Volumes/adcock_lab/main/user_folders/jeff/development/')
	
	orig_dir, orig_fname = os.path.split(input_path)
	orig_fname_header, dot, extension = orig_fname.partition('.')
	
	if extension == 'hdr':
		hdr_path = os.path.join(orig_dir, (orig_fname_header+'.hdr'))
		img_path = os.path.join(orig_dir, (orig_fname_header+'.img'))

		# copy original to working directory (if the original file isn't already being picked from the working directory)
		if orig_dir is not data_dir: 
			shutil.copy(hdr_path, data_dir)
			shutil.copy(img_path, data_dir)

		# convert to nifti
		cmd_str = ('fslchfiletype NIFTI_GZ ' + os.path.join(data_dir, orig_fname_header))
		os.system(cmd_str)
	
	elif extension == 'nii.gz':
		nii_path = os.path.join(orig_dir, (orig_fname_header+'.nii.gz'))
		
		# copy the nifti image to the working directory
		shutil.copy(nii_path, data_dir)
	
	# name of the local nifti copy of the desired image
	nifti_file = os.path.join(data_dir, (orig_fname_header + '.nii.gz'))
	print nifti_file
	
	# open the nifti image
	ds = nib.load(nifti_file)
	
	# extract pixel data
	ds_data = ds.get_data()	
	n_slices = ds_data.shape[2]
	
	# put the data into the correct format for sending out the socket connection
	scan_images = []
	for t in range(0, ds_data.shape[3]):
		for s in range(0, ds_data.shape[2]):
			this_slice = ds_data[:,:,s,t]
			
			# ds_data is read in assuming (x,y,z,t) orientation. fScan sends slices in (y,z). Thus, we must transpose first
			this_slice = this_slice.T
			
			# flatten slice to 1D
			flattened_slice = this_slice.flatten()
			
			# convert dtype to int16 if not already (int 16 is the format of images coming off the scanner)
			if flattened_slice.dtype != 'int16':
				flattened_slice.dtype = 'int16'
			
			# convert flattened array to binary string, append to scan_images
			slice_as_binary = flattened_slice.tostring()
			scan_images.append(slice_as_binary)

	# ask for the TR
	TR = raw_input('what is the TR? (in Sec): ')

	# print loading message to screen
	print 'building volume....' 
	
	# save in the scanSim/data dir
	save_fname = file(os.path.join(data_dir,'saved_nifti_volume.pkl'), 'w')
	vars_to_save = [scan_images, input_path, n_slices, TR]
	pickle.dump(vars_to_save, save_fname)
	save_fname.close()
	print 'Image volume built....'


# print parameters before beginning
print '-----------------------------------------------'
print ('Original file: ' + input_path)
print ('# slices: ' + str(n_slices))
print ('TR: ' + str(TR))
print ('host: ' + host)
print ('port: ' + str(port))
if len(sys.argv) == 2:
	if sys.argv[1] == '-f':										# set the delay to 0 if that argument is specified
		delay = 0
	else:
		delay = np.true_divide(int(TR), n_slices)				# set the time to pause between slice transmissions, in order to match acquisition rate
		delay = float(delay)
else:
	delay = np.true_divide(int(TR), n_slices)				# set the time to pause between slice transmissions, in order to match acquisition rate
	delay = float(delay)
print 'interslice delay : ' + str(delay)
print '-----------------------------------------------'

# speed up delay slightly
delay = .75*delay


# CONNECT TO SERVER SOCKET
socket_obj = socket(AF_INET, SOCK_STREAM)			# create new socket connection
socket_obj.connect((host, port))					# connect to the socket


# send open message, wait for response from server
opn_msg = '<opn c="1" t="416" x="64" y="64" z="' + str(n_slices) + '"/>\n\r'
sent_opn = socket_obj.send(opn_msg)
print '<opn> message sent'
get_ack = socket_obj.recv(sent_opn)
if len(get_ack) == sent_opn: 
	print 'Server acknowledged <opn> message'

# BUILT IN FUNCTIONS	
def get_xml_val(tag, xml_string):						# searches the xml_string for the specified tag, returns tag value as integer
	found_value = re.search((tag+'="(\d*)"'), xml_string)
	if not found_value: print 'ERROR: getting ', tag, ' value from ', xml_string
	else:
		return int(found_value.group(1))

# LOOP THROUGH ALL IMAGES
print 'Press ENTER to send'
wait = raw_input()
start = time.time()				# start time
for slice_image in range(len(scan_images)):
	image_data = scan_images[slice_image]
	image_size = len(image_data)
	
	# BUILD XML-HEADER
	xml_end = (' c="1" t="i" f="b" v="' + str(v) + '" z="' + str(z) + '" n="' + str(image_size) + '"/>\n\r')
	xml_beginning = ('<rec L="' + str(len(xml_end)+14).zfill(5) + '"')
	xml_string = xml_beginning + xml_end
	print xml_string
	
	# SEND XML HEADER
	sent_xml = socket_obj.send(xml_string)	
	#print xml_string, ' bytes: ', str(len(xml_string))
	
	# SEND IMAGE DATA VIA SOCKET
	while True:
		sent_image = socket_obj.send(image_data)
		#print 'Sent image data ', str(sent_image), ' bytes long'
		get_ack = socket_obj.recv(len(xml_string))
		print get_ack
		ack_bytes = get_xml_val('n', get_ack)
		if ack_bytes == sent_image: break
		

	z += 1 			# increment slice by 1
	if z == (n_slices+1):
		v += 1		# increment vol by 1
		z = 1		# reset slice
	time.sleep(delay)

end_msg = '<end c="1" n="' + str(len(scan_images)/n_slices) + '">\n\r'
sent_end = socket_obj.send(end_msg)
print 'sent <end>'
end = time.time()

get_ack = socket_obj.recv(sent_end)
if len(get_ack) == sent_end:
	print 'Server acknowledged <end> message. Connection closing'
	socket_obj.close()

print 'total time:', str(end-start)
print ' time/slice: ', str((end-start)/(len(scan_images)))

