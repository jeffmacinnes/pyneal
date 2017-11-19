#!/usr/bin/env python
# encoding: utf-8
"""
plotter.py
generic plotting class. Instances of this class can be used to 
plot things like real-time motion output or statistical output

-jjm 8/1/2013

"""

import sys
import os
import time
import string
import subprocess
import fnmatch
import signal
import tempfile
import threading
import numpy as np


class Plotter(threading.Thread):
	"""
	Generic plotting class
	--------------------
	this class can be used to create instances of specific plots
	for use within Pyneal. Plotting is done by passing string commands 
	to Gnuplot. Make sure Gnuplot is installed and functional on your
	operating system
	
	-create an instance of the plot with:
		myplot = plotter.Plotter(title="My Plot Title", n_Ys, data_labels=["A", "B", "C"], Xrange=np.array([0,50]), Yrange=np.array([-5,5]))
		
		input args:
			title: title of your plot [defaults to "Plot"]
			n_Ys: number of independent data sources plotted
			data_labels: list of labels associated with each data source [defaults to "None"]
				*NOTE: if included, number of list items in data_labels must match n_Ys
			Xrange: numpy array specifying x-axis min and max [defaults to None, or autoscale]
			Yrange: numpy array specifying y-axis min and max [defaults to None, or autoscale] 
				
	-update the plot with:
		myplot.update(new_data)
		
		input args:
			new_data: numpy array containing new data to be plotted
	"""
	
	def __init__(self, plot_title="Plot", n_Ys=1, data_labels=None, Xrange=None, Yrange=None):
		threading.Thread.__init__(self)
		self.pyneal_dir = os.path.abspath(os.path.dirname(sys.argv[0]))
		
		# configuration vars
		self.n_Ys = n_Ys
		self.line_num = 0					# initialize line number counter. line number will serve as x-vales and will be written as the leftmost column in the tempfile
		self.plot_title = plot_title
		self.data_labels = data_labels
		
		# set up temp file
		self.tmp_file = tempfile.NamedTemporaryFile(mode='a+', suffix='.gnuplot', dir=self.pyneal_dir, delete=True)			# open tempfile in append & read mode
		
		# initialize plot
		self.plot = subprocess.Popen(['gnuplot', '-persist'], shell=True, stdin=subprocess.PIPE, preexec_fn=os.setsid)
		self.plot.stdin.write('set grid\n')
		self.plot.stdin.write(('set title "' + self.plot_title + '" \n'))
		if Xrange is not None:
			self.Xrange = '[%s:%s]' % (str(Xrange[0]), str(Xrange[1]))
			self.plot.stdin.write(('set xrange ' + self.Xrange + '\n'))
		if Yrange is not None:
			self.Yrange = '[%s:%s]' % (str(Yrange[0]), str(Yrange[1]))
			self.set_autoscaleY = false
		else:
			self.Yrange = '[%s:%s]' % (str(-3), str(3))							# set default to initially be +/- 3, then set to autoscale later
			self.set_autoscaleY = True
		self.plot.stdin.write(('set yrange ' + self.Yrange  + '\n'))
		
		# create an empty plot 
		self.open_plot()
	
	def open_plot(self):
		"""
		method to create an empty plot before the run actually starts. Subsequent calls to 'update_plot'
		will overwrite this plot
		"""
		# write a datapoint that exceeds the plot range
		self.plot.stdin.write(('set key off \n'))
		plot_cmd = 'plot 100 with lines'
		self.plot.stdin.write((plot_cmd + '\n'))
		
		# turn back on settings that you want once real plotting begins
		self.plot.stdin.write('set key on \n')
		if self.set_autoscaleY:
			self.plot.stdin.write('set autoscale y \n')
		
	def update_plot(self, new_data):
		"""
		method to update the plot. 
		First, the new data will be written to the tempfile
		(on a new line with the next line number in the leftmost column)
		
		Next, the entire temp file contents will be read. Based on the number of columns
		the appropriate plot command strings will be written and concatenated together into 
		a single gnuplot command
		
		Lastly, the command is written to the gnuplot PIPE and the plot will update with all 
		of the new data
		"""
		self.line_num += 1								# increment the line number counter by 1
		
		#### WRITE DATA TO TEMP FILE
		new_line = string.join(['%.5s' % x for x in new_data], ' ')
		self.write2temp(self.tmp_file, new_line)
		
		#### READ DATA FROM TEMP FILE, REPLOT
		self.tmp_file.seek(0)												# move file pointer to beginning of file
		fname = '"%s"' % self.tmp_file.name									# store temp file name as string with quotes
		gnuplot_cmd = 'plot'												# begin gnuplot command
		plot_cmds = []														# empty array to build individual plot commands into
		# for each column in the data file, build line 
		for i,col_index in enumerate(range(2, self.n_Ys+2)):
			if self.data_labels:
				this_label = '"%s"' % self.data_labels[i]					# format label, if specified
			else:
				this_label = '"%s"' % str(i+1)
			this_plot_cmd = string.join([fname, ('u 1:' + str(col_index)), ('t ' + this_label), 'w lines'], ' ')	# build full command for specific plot
			plot_cmds.append(this_plot_cmd)
		gnuplot_cmd = string.join([gnuplot_cmd, ','.join(plot_cmds), '\n'], ' ')		# contatanate all plot commands together for single gnuplot call
		self.plot.stdin.write(gnuplot_cmd) 												# write command to gnuplot PIPE
			
	def write2temp(self, filename, line):
		"""
		method to write new lines of data to the temporary file
		"""
		self.line = string.join([str(self.line_num), line, '\n'], ' ')		# append 'return' on to end of line
		filename.write(self.line)
	
	def close_plot(self):
		"""
		method to stop the GNUPLOT subprocess and 
		remove the temp file
		"""
		os.killpg(self.plot.pid, signal.SIGTERM)
		self.tmp_file.close()
		


