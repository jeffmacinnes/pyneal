#!/usr/bin/env python
# encoding: utf-8
"""
receiver.py
-jjm 3/8/11

Module for receiving incoming fMRI data via socket connection
Data are expected to arrive as slices, with 2 transmissions/slice:
the first sends an xml-header with information about the slice
about to be sent. The second is the binary slice data itself, 
which is decoded as 16-bit unsigned integers and placed into a 
prespecified 4d matrix at the appropriate location

Note: fScan sends the slice data in [y,x] format. This module recieves 
that data and write it into a 4d matrix in the form [t,z,y,x]. When the
stat module requests a specific timepoint, it is transposed from [z,y,x]
to [x,y,z]

"""
import os
import sys
import fnmatch
import glob
import numpy as np
import time
import re
import struct
import select
import array
from socket import *
import threading


class Receiver(threading.Thread):
	"""
	The Receiever class is set to run in a separate thread
	and listen for incoming slice data over a socket connection.
	This section will need to be modified to match the environment
	at any given scanner facility
	"""
	def __init__(self, host, port, n_tmpts):
		threading.Thread.__init__(self)									# initialize the thread
		self.host = host												# initialize the host variable
		self.port = port												# initialize the port variable
		self.n_tmpts = n_tmpts
		self.volume = 0													# initialize the volume variable
		self.slice_n = 0												# initialize the slice variable
		self.last_completed_vol = 0										# initialize the last_completed_vol variable
		self.fixed_xml_buf = 14											# specify the size in bytes for the first xml read
		self.volume_start_times = np.zeros(self.n_tmpts)
		self.kill_socket = 0											# initialize kill_socket option
		self.isAlive = False
		
	def run(self):												# receive slices over socket sent from fSCAN
		# ESTABLISH CONNECTION WITH CLIENT
		self.sockobj = socket(AF_INET, SOCK_STREAM)
		self.sockobj.bind((self.host, self.port))
		self.sockobj.listen(1)
		print 'Waiting to connect to scanner...'
		while True:
			if self.kill_socket == 0:
				inputready, outputready, exceptready = select.select([self.sockobj], [], [],1)
				for s in inputready:
					if s == self.sockobj:
						self.connection, self.address = self.sockobj.accept()
						print 'Receiver connected by', self.address	
						self.isAlive = True
			else: 
				sys.exit()
			if self.isAlive:break
		
		# WAIT FOR '<opn...>' MESSAGE
		print 'Waiting for <opn ...> message'
		while True:																	# wait for opn message. 
			self.opn_msg = self.connection.recv(256)				
			if self.opn_msg.find('opn') != -1:										# once received, substitute 'opn' with 'ack, and resend					
				print 'Received <opn...> request'
				self.opn_reply = self.connection.send(self.opn_msg.replace('opn', 'ack'))
				break
			
		self.n_slices = self.get_xml_val('z', self.opn_msg)							# get z-value from <opn> xml string
		self.slice_y = self.get_xml_val('y', self.opn_msg)							# get y-value from <opn> xml string
		self.slice_x = self.get_xml_val('x', self.opn_msg)							# get x-value from <opn> xml string
		self.image_matrix = np.zeros(shape=(self.n_tmpts, self.n_slices, self.slice_y, self.slice_x))	# build empty data matrix
		print 'Ready to begin the scan...'
		
		# READ ALL INCOMING IMAGE DATA, DECODE BINARY, WRITE TO VARIABLE
		while True:
			# read xml header
			# read the start of the xml header
			self.xml_start = ''
			self.xml_start_remaining = self.fixed_xml_buf
			while len(self.xml_start) < self.fixed_xml_buf and self.isAlive:		# read from the socket until the start buffer is filled
				self.xml_start = self.xml_start + self.connection.recv(self.xml_start_remaining)
				self.xml_start_remaining = self.fixed_xml_buf - len(self.xml_start)
				
			if self.xml_start.find('end') != -1:									# if the <end> msg is found,
				self.xml_remaining = self.connection.recv(100)						# read the rest of it, 
				self.end_msg = self.xml_start + self.xml_remaining					# concatenate parts, 
				print self.end_msg
				self.n_vols_sent = self.get_xml_val('n', self.end_msg) 				# get however many volumes it *thinks* were sent,
				self.n_vols_recvd = self.get_last_completed_vol()					# get how many volumes were received,
				self.end_ack = self.end_msg.replace('end', 'ack').replace(str(self.n_vols_sent), str(self.n_vols_recvd))
				try:
					self.end_reply = self.connection.send(self.end_ack)				# send the end acknowledgement reply
				except:
					pass															# don't fret if fscan already closed the socket
				self.close_socket()													# close the socket
				print '<end> message received'
				break			
			self.xml_size = self.get_xml_val('L', self.xml_start)					# get byte size of xml string 
			
			# read the remainder of the xml header (the tail)
			self.xml_tail_size = self.xml_size-self.fixed_xml_buf					# calculate the expected length of the xml tail
			self.xml_tail_remaining = self.xml_tail_size
			self.xml_tail = ''						
			while len(self.xml_tail) < self.xml_tail_size and self.isAlive:			# keep reading until you get the full tail
				self.xml_tail = self.xml_tail + self.connection.recv(self.xml_tail_remaining)
				self.xml_tail_remaining = self.xml_tail_size - len(self.xml_tail)

			self.xml_header = self.xml_start + self.xml_tail						# concatenate xml string parts
			#print self.xml_header
			
			# get values from xml header
			self.expected_bytes = self.get_xml_val('n', self.xml_header)			# retrieve the byte size tag from xml header
			self.volume = self.get_xml_val('v', self.xml_header)					# retrieve the volume number from xml header
			self.slice_n = self.get_xml_val('z', self.xml_header)					# retrieve the slice number from xml header
			if self.volume == 1 and self.slice_n == 1:
				print 'Scan started...'
			
			# update the start time of volume transmission
			if self.slice_n == 1:
				self.volume_start_times[self.volume-1] = time.time()
			
			# read image data, send <ack> reply specifying how many bytes recv'd
			self.image_data = ''
			self.bytes_remaining = self.expected_bytes
			while len(self.image_data) < self.expected_bytes:
				self.image_data = self.image_data + self.connection.recv(self.bytes_remaining)
				self.image_ack = self.xml_header.replace('rec', 'ack').replace(str(self.expected_bytes), str(len(self.image_data)))
				self.bytes_remaining = self.expected_bytes - len(self.image_data)
				try:
					self.image_reply = self.connection.send(self.image_ack)
				except:
					# note: after the last slice, fscan may close the socket before receiving the ACK, and 
					# this script will crash without properly closing the sockets. This try/except bit prevents that
					pass
			# decode binary image data, reshape to 2D matrix, write to image_matrix
			self.unpacked_image = struct.unpack((str(self.expected_bytes/2) + 'H'), self.image_data)	# unpack as 16-bit unsigned integers
			self.array = np.array(self.unpacked_image)								# write unpacked data to numpy array
			self.array = np.reshape(self.array, (self.slice_y, self.slice_x))		# reshape according to slice dimensions
			self.image_matrix[(self.volume-1)][(self.slice_n-1)][:][:] = self.array	# write slice data into 4D image matrix (NOTE: indexing starts at 0) order will be [t][z][y][x]
				
			# update variables
			if self.slice_n == self.n_slices:							# update last_completed_volume variable
				self.last_completed_vol = self.volume
	
	def get_xml_val(self, tag, xml_string):								# return the requested tag value from the xml-string
		self.found_value = re.search((tag + '="(\d*)"'), xml_string)
		if not self.found_value: print 'ERROR getting ', tag, ' value from ', xml_string
		else:
			return int(self.found_value.group(1))			

	def is_started(self): 												# check whether data has started to arrive or not
		if self.volume >= 1 & self.slice_n >= 1:
			return True
		else: 
			return False
	
	def is_finished(self):												# check whether ALL expected data has arrived
		if self.last_completed_vol == self.n_tmpts:
			return True
	
	def get_last_completed_vol(self):									# get the most recently completed volume number
		return (self.last_completed_vol)
			
	def get_volume(self, desired_vol):									# grab all slices from the specified volume (NOTE: returns volume in (x,y,z) orientation)
		self.requested_volume = self.image_matrix[(desired_vol-1)][:][:][:] # NOTE: indexing starts at 0
		return self.requested_volume.T									# Convert the volume dimensions from (z,y,x) to (x,y,z)
	
	def get_volume_start_times(self):
		return self.volume_start_times
	
	def get_n_slices(self):												# returns the number of slices in image aquisition
		return self.n_slices
		
	def	get_latest_data(self):											# grab all volumes from the 4D matrix
		return self.image_matrix
	
	def close_socket(self):												# close the connection
		print 'Receiver socket closed'
		self.kill_socket = 1
		if self.isAlive:
			self.connection.close()
			self.isAlive = False
		#sys.exit()	
