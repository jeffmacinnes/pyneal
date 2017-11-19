#!/usr/bin/env python
# encoding: utf-8
"""
log_window.py

Jeff MacInnes -- 2013-06-27.

Class to create new instances of X11 windows. With the new windows, you can direct specific output
to each, enabaling you to monitor specific on-going processes during a real-time run

"""

import sys
import os
from subprocess import Popen, PIPE
import random
import time

class LogWindow():
	def __init__(self, name):
		"""
		Initialize a new logging window. Supply a name (string) to give to the new pipe
		"""
		self.pipe_path = ("/tmp/pyneal_PIPE_" + name)
	
		# create the pipe if not already existing
		if not os.path.exists(self.pipe_path):
			os.mkfifo(self.pipe_path)
		
		# open a new Xterm window
		self.create_win(name)
		
	def create_win(self, title):
		# open new Xterm win
		self.win = Popen(['xterm', '-title', title, '-e', 'tail', '-f', self.pipe_path])
		
	def write_log(self, log_message):
		try:
			this_pipe = open(self.pipe_path, "w")
			message = (log_message + '\n')
			this_pipe.write(message)
			this_pipe.close()
		except:
			pass
		
	def close_pipe(self):
		# delete the temporary pipe file associated with each log, kill the open window
		os.remove(self.pipe_path)
		self.win.kill()