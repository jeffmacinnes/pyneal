#!/usr/bin/env python
"""
motion.py
motion calculations
"""

import os
import sys
import numpy as np
import time
import Gnuplot
import string
import subprocess

import tempfile, types
try:
	from cStringIO import StringIO
except ImportError:
	from StringIO import StringIO

# set up data
x_range = '[0:100]'
y_range = '[0:2500]'
x = np.arange(100)
y1 = np.sin(x)
y2 = np.random.randn(100)
y3 = .01*x

# intialize plot
#g = Gnuplot.Gnuplot(persist=1)
#g('set terminal X11')
#g('set grid')
#g(('set xrange ' + x_range))
#g('set samples 200')
#g('set key top right')
#g(('set yrange ' + y_range))

tmp = open('plot.dat', 'w')
plot = subprocess.Popen(['gnuplot', '-persist'], shell=True, stdin=subprocess.PIPE)
plot.stdin.write('set grid\n')
plot.stdin.write('set xrange [0:100]\n')
tmp.close()

for i in x:
	if i > 2:
		tmp = open('plot.dat', 'a')
		tmp.write(string.join([str(x[i]), str(y1[i]), str(y2[i]), '\n'], '\t'))
		tmp.close()
		#d1 = Gnuplot.Data(x[:i], y1[:i], with_='l', title='X')
		#d2 = Gnuplot.Data(x[:i], y2[:i], with_='l', title='Y')
		#d3 = Gnuplot.Data(x[:i], y3[:i], with_='l', title='Z')
		#g.plot(d1,d2,d3, title='motion parameters')
		plot.stdin.write('plot "plot.dat" using 1:3 with lines \n')
		time.sleep(.01)
tmp.close()
raw_input('Please press return to quit...\n')

def Data():
	"""
	from GnuPlot.py
	basically, writes the numpy data to temp file which is then returned
	
	then you call plot and supply it each of the temp files that is returned
	
	have gnuplot read from a Popen PIPE
	"""
	f = StringIO()
	utils.write_array(f,data)
	content = f.getvalue()
	return _NewFileItem(content)


class _NewFileItem(_FileItem):
    def __init__(self, content, filename=None, **keyw):

        binary = keyw.get('binary', 0)
        if binary:
            mode = 'wb'
        else:
            mode = 'w'

        if filename:
            # This is a permanent file
            self.temp = False
            f = open(filename, mode)
        else:
            self.temp = True
            if hasattr(tempfile, 'mkstemp'):
                # Use the new secure method of creating temporary files:
                (fd, filename,) = tempfile.mkstemp(
                    suffix='.gnuplot', text=(not binary)
                    )
                f = os.fdopen(fd, mode)
            else:
                # for backwards compatibility to pre-2.3:
                filename = tempfile.mktemp()
                f = open(filename, mode)

        f.write(content)
        f.close()

        # If the user hasn't specified a title, set it to None so
        # that the name of the temporary file is not used:
        if self.temp and 'title' not in keyw:
            keyw['title'] = None

        _FileItem.__init__(self, filename, **keyw)

    def __del__(self):
        if self.temp:
            os.unlink(self.filename)