""" Main Start-Up Script """

import os
import subprocess
from Tkinter import *

### Config Vars
buttonWidth = 20;

### GUI Sections
def createLogo(parentFrame):
	""" create logo box """
	logoFrame = Frame(parentFrame)
	logoDir = os.path.join(pyneal_dir, 'docs/images')
	logoImg = PhotoImage(file=os.path.join(logoDir, 'logoMain.gif'))
	logoLabel = Label(logoFrame, image=logoImg)
	logoLabel.image = logoImg			# need to store reference to it

	# pack components
	logoLabel.pack(side=TOP)
	logoFrame.pack(side=TOP)

def createScan(parentFrame):
	""" create frame for scan utilities """
	scanFrame = LabelFrame(parentFrame, text='Scanning')
	scanButton = Button(scanFrame, 
						text='Real-time Scan',
						width=buttonWidth,
						pady=10,
						command=launchScan)

	# pack components
	scanButton.pack()
	scanFrame.pack(padx=2, pady=2, expand=YES, fill=X)

def createUtilities(parentFrame):
	""" create frame for additional utilities """
	utilFrame = LabelFrame(parentFrame, text='Utilities')

	# utilty buttons
	roiConvertButton = Button(utilFrame,
						text='ROI MNI2func',
						width=buttonWidth,
						command=launchROI_mni2func).pack(side=TOP)
	getDataButton = Button(utilFrame, 
						text='Get series from scanner',
						width=buttonWidth, 
						command=launchGetFromScanner).pack(side=TOP)

	# pack parent frame
	utilFrame.pack(padx=2, pady=10, expand=YES, fill=X)

def createQuit(parentFrame):
	""" create frame for the quit button """
	quitFrame = Frame(parentFrame)
	quitButton = Button(quitFrame, 
						text='Exit',
						width=int(.5*buttonWidth),
						command=quitPyneal).pack(side=TOP)
	# pack parent frame
	quitFrame.pack(padx=2, pady=5, expand=YES, fill=X)


### Button functions
def launchScan():
	subprocess.Popen(['python', 'src/pynealScan.py'])

def launchROI_mni2func():
	""" run the roi_mni2func.py script """
	subprocess.Popen(['python', 'utils/roi_mni2func.py'])

def launchGetFromScanner():
	""" run the getFromScanner.py script """
	print ' '
	subprocess.Popen(['python', 'utils/getFromScanner.py'])

def quitPyneal():
	sys.exit()


### Main Loop
if __name__ == '__main__':

	pyneal_dir = os.path.abspath(os.path.dirname(__file__))
	print pyneal_dir

	# start building GUI
	root = Tk()
	root.title('Pyneal')

	# create the main parent frame
	rootFrame = Frame(root)
	rootFrame.pack()

	# create/populate the seperate sections
	createLogo(rootFrame)
	createScan(rootFrame)
	createUtilities(rootFrame)
	createQuit(rootFrame)

	# run the GUI
	root.mainloop()
	
	
