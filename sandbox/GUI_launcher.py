### pretend this is the main pyneal script
# it needs to be able to read settings, and launch
# the webserver, and open a GUI that goes to that window

import webbrowser
import GUI.webserver as pynealGUI

# read settings
settings = {}
settings['name'] = 'jeff'
settings['age'] = 33



pynealGUI.startServer()
