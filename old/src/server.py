#!/usr/bin/env python
# encoding: utf-8
"""
Server.py

Created by Jeff MacInnes on 2011-08-05.
Server class for use with pyneal real-time software
Server will listen for incoming requests, look up the requested information, and reply.
The real-time computer will send output to the presentation computer only
when requested. When idle, the server will sit listening on a separate thread

"""

import sys
import os
import time
from socket import *
import numpy as np
import threading
import select
from log_window import *

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

		# set up logging window
		self.serverLog = LogWindow('Server Monitor')
		self.serverLog.write_log("Server Log:")

	def run(self):
		self.start_server()											# start the socket server loop

	def start_server(self):
		self.sockobj = socket(AF_INET, SOCK_STREAM)					# create new socket object
		#self.sockobj.settimeout(1)
		self.sockobj.bind((self.host, self.port))
		self.sockobj.listen(1)
		print 'Export server alive and listening...'
		while True:
			try:
				self.connection, self.address = self.sockobj.accept()	# accept new connection, redirect to new socket
				self.request = self.connection.recv(100)				# receieve message from connection (max 100 bytes)
				self.serverLog.write_log('received request for: ' + self.request.strip('\n'))
				self.answer = self.request_lookup(int(self.request))	# lookup the requested answer
				self.connection.send(self.answer)						# send the answer back to the client
				self.connection.close()									# close the socket
				self.serverLog.write_log('sent ' + self.answer.strip('\n') + ' for vol ' + str(self.request))
			except:
				if self.kill_thread:
					self.close_socket()
					sys.exit()
				else: pass

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
		self.serverLog.close_pipe()									# close the server monitor window
		print 'Export server socket closed'
