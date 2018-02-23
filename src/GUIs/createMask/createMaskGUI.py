"""
Create Mask GUI:
GUI to set inputs and option for creating a mask to use during Pyneal real-time
analysis. Pyneal requires that all masks be in subject functional space; this
tool helps create those.

All of the settings are stored in a createMaskConfig.yaml file. This GUI reads
that file to obtain initial settings, and then once the user hits 'submit' the
file is overwritten with new settings
"""
import os
from os.path import join
import sys

import yaml

from kivy.app import App
from kivy.uix.widget import Widget
from kivy.uix.label import Label
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.textinput import TextInput
from kivy.properties import StringProperty, NumericProperty, ListProperty, ObjectProperty, DictProperty
from kivy.uix.filechooser import FileChooserListView
from kivy.uix.popup import Popup
from kivy.factory import Factory



# Set Window Size
from kivy.config import Config
Config.set('graphics', 'width', '400')
Config.set('graphics', 'height', '500')

# initialize global var that will store path to createMaskConfig.yaml file
createMaskConfigFile = None


class MainContainer(BoxLayout):
    """
    Root level widget for the createMask GUI
    """
    # create a kivy DictProperty that will store a dictionary with all of the
    # settings for the GUI.
    GUI_settings = DictProperty({}, rebind=True)
    setupGUI_dir = os.path.dirname(os.path.abspath(__file__))
    print(setupGUI_dir)
    textColor = ListProperty([0,0,0,1])


class CreateMaskGUIApp(App):
    """
    Root App class. This will look for the createMaskGUI.kv file in the same
    directory and build the GUI according to the parameters outlined in that file.
    Calling 'run' on this class instance will launch the GUI
    """
    title = 'Create Mask'
    pass


# Register the various components of the GUI
Factory.register('MainContainer', cls=MainContainer)

def launchCreateMaskGUI(settingsFile):
    """
    launch the createMask GUI. Call this function to open the GUI. The GUI will
    be populated with the settings specified in the 'settingsFile'.

    settingsFile: path to yaml file containing createMaskConfig settings
    """
    global createMaskConfigFile
    createMaskConfigFile = settingsFile

    # launch the app
    CreateMaskGUIApp().run()



# for testing purposes, you can launch the GUI directly from the command line
if __name__ == '__main__':
    # path to config file
    settingsFile = 'createMaskConfig.yaml'

    # launch GUI
    launchCreateMaskGUI(settingsFile)
