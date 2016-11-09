#!/usr/bin/env python
# encoding: utf-8
"""
outputSim.py

Jeff MacInnes -- 2013-06-17

This script will simulate a stream of output values generated from Pyneal. 

An array of output values will be generated according to the parameters specified

The server will listen for incoming requests from the matlab presenation script and 
reply as apporpriate. 

"""

import sys
import os
from socket import *
import numpy as np 
import threading
import select
import time

# Socket Settings
#host=gethostbyname(gethostname())
host = '127.0.0.1'
port=61000

# output distribution settings
mean = 15
stdDev = 3
n_samples = int(raw_input('how many samples? '))
print 'Host: ' + host
print 'Port: ' + str(port)
print '# samples: ' + str(n_samples)
print 'mean: ' + str(mean)
print 'std: ' + str(stdDev)

############ IN-SCRIPT FUNCTIONS/CLASSES
class Server(threading.Thread):
	def __init__(self, host, port):
		"""
		Initialize a new thread that will handle calls to the Server. The server will take requests, 
		and check to see if the requested volume has arrived. If it has, it will return the stat
		output for that volume to the client. If not, it will return a 'N' to the client.
		"""
		
		# spawn a new thread
		threading.Thread.__init__(self)
		self.setDaemon(True)
		
		# CONFIGURATION VARIABLES
		self.host = host
		self.port = port
		self.most_recent_vol = 0									# initialize the most_recent_vol variable
		self.kill_thread = 0
		
	def run(self):
		self.start_server()											# start the socket server loop
		while not self.kill_thread:
			read_sockets, write_sockets, exceptions = select.select( [self.sockobj], [], [])
			if read_sockets:
				print 'Export server is waiting for connection...'
				self.connection, self.address = self.sockobj.accept()	# accept new connection, redirect to new socket
				self.request = self.connection.recv(100)				# receieve message from connection (max 100 bytes)
				self.request = int(self.request)						# convert to integer. 'request' assumed to be a time pt
				self.answer = self.request_lookup(self.request)			# lookup the requested answer
				self.connection.send(self.answer)						# send the answer back to the client
				self.connection.close()									# close the socket

	def start_server(self):
		self.sockobj = socket(AF_INET, SOCK_STREAM)					# create new socket object
		self.sockobj.bind((self.host, self.port))
		self.sockobj.listen(1)
		print 'Export server alive and listening...'
		while True:
			self.connection, self.address = self.sockobj.accept()	# accept new connection, redirect to new socket
			self.request = self.connection.recv(100)				# receieve message from connection (max 100 bytes)
			print 'received request for: ' + self.request.strip('\n')
			self.request = int(self.request)						# convert to integer. 'request' assumed to be a time pt
			self.answer = self.request_lookup(self.request)			# lookup the requested answer
			self.connection.send(self.answer)						# send the answer back to the client
			self.connection.close()									# close the socket
			print 'sent ' + self.answer.strip('\n') + ' for vol ' + str(self.request) + '\n'
			
		
	def update_server(self, most_recent_vol, output_values):
		self.most_recent_vol = most_recent_vol						# store the most recent volume from the receiver 
		self.output_values = output_values							# store the existing output values
	
	def request_lookup(self, request):
		"""
		checks to see if the requested volume has arrived yet. If so, return the stat output.
		If not, return 'N'	
		"""
		if request > self.most_recent_vol:
			self.answer = 'N'
		else:
			self.answer = str(self.output_values[request-1])		# NOTE: indexing starts at 0. hence the "- 1"
		self.answer = (self.answer + '\n')							# append a newline character to the message
		return self.answer
		
	def close_socket(self):
		self.kill_thread = 1										# flip the kill_thread switch
		self.sockobj.close()										# close the server socket
		print 'Export server socket closed'
		
############ BEGIN SCRIPT

this_dir = os.path.abspath(os.path.dirname(sys.argv[0]))
save_fname = 'outputSIM_output.txt'

# generate values
output_source = np.random.normal(loc=mean, scale=stdDev, size=n_samples)
trend = np.linspace(0,5,num=n_samples)
output_source = output_source + trend
np.savetxt(os.path.join(this_dir, save_fname), output_source, fmt='%.3f')

# start the server
server = Server(host, port)
server.start()

# press to begin the server
time.sleep(.5)
raw_input('Press ENTER to start run \n')

# populate the output values in the server
output_values = np.zeros(n_samples)
most_recent_vol = 0
for vol in range(n_samples):
	output_values[vol] = output_source[vol]
	most_recent_vol += 1
	server.update_server(most_recent_vol, output_values)
print 'output values created....'

# wait for user input before quitting
raw_input('press ENTER to quit')
server.close_socket()