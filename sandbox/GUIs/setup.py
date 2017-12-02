"""
Pyneal Setup GUI:
Pyneal is configured using settings stored in a setupConfig.yaml file in the root
dir. This setup GUI is basically just a way to view the current settings as specified
by that file, as well as a convenient way for users to update those settings to
fit the parameters of a particular experiment.

When pyneal is launched, it'll first open this GUI and give users a chance to
verify/change the current settings. When the user hits 'Submit', the settings
from the GUI will be re-written to the setupConfig.yaml file, and subsequent
stages of pyneal will read from that file.

Users should not need to edit the setupConfig.yaml file directly. Instead, they
can make a custom .yaml file with any of the Pyneal settings they wish to specify,
and load that file from within the GUI. Any setting specified by this file will
overwrite the current GUI value; all other settings will be taken from the
setupConfig.yaml file. This is a way for users to keep unique settings files for
different experiements.
"""
import os
import sys

import yaml

from kivy.app import App
from kivy.uix.widget import Widget
from kivy.uix.boxlayout import BoxLayout
from kivy.properties import StringProperty, NumericProperty, ObjectProperty, DictProperty
from kivy.storage.jsonstore import JsonStore
from kivy.uix.filechooser import FileChooserListView
from kivy.uix.popup import Popup
from kivy.factory import Factory
from kivy.clock import Clock

# Set Window Size
from kivy.config import Config
Config.set('graphics', 'width', '400')
Config.set('graphics', 'height', '700')

# initialize global var that will store path to the setupConfigFile
setupConfigFile = None

class LoadSettingsDialog(BoxLayout):
    loadSettings = ObjectProperty(None)
    cancelSettings = ObjectProperty(None)


class MainContainer(BoxLayout):
    """
    Custom widget that is the root level container for all
    other widgets
    """
    # create a kivy DictProperty that will store a dictionary with all of the
    # settings for the GUI.
    GUI_settings = DictProperty({}, rebind=True)

    def __init__(self, **kwargs):
        self.GUI_settings = self.readSettings(setupConfigFile)

        # pass the keywords along to the parent class
        super().__init__(**kwargs)

        # populate the GUI according to the settings. Many of the text
        # settings (e.g. scanner port) read directly from GUI_settings,
        # and will update automatically. But other
        self.populateGUI(self.GUI_settings)


    ### Methods for dealing with loading/saving Settings -----------------------
    def readSettings(self, settingsFile):
        """
        Open the supplied settingsFile, and compare to the default
        values. Any valid setting in the settingsFile will override
        the default
        """
        # set up defaults. Store the value and the dtype. This is used
        # to confirm that a loaded setting is valid
        defaultSettings = {
            'scannerPort': [999, int],
            'outputPort': [999, int],
            'numTimepts': [999, int],
            'statsChoice': ['Median', str]
            }

        # initialize dictionary that will eventually hold the new settings
        newSettings = {}

        # load the settingsFile, if it exists
        if os.path.isfile(settingsFile):
            # open the file, load all settings from the file into a dict
            with open(settingsFile, 'r') as ymlFile:
                loadedSettings = yaml.load(ymlFile)

            # Go through all default settings, and see if there is
            # a loaded setting that should overwrite the default
            for k in defaultSettings.keys():
                # does this key exist in the loaded settings
                if k in loadedSettings.keys():
                    loadedValue = loadedSettings[k]

                    # does the dtype of the value match what is
                    # specifed by the default?
                    if type(loadedValue) == defaultSettings[k][1]:
                        newSettings[k] = loadedValue
                    else:
                        # throw error and quit
                        print('Problem loading the settings file!')
                        print('{} setting expecting dtype {}, but got {}'.format(
                                k,
                                defaultSettings[k][1],
                                type(loadedValue)
                                ))
                        sys.exit()
                # if the loaded file doesn't have this setting, take the default
                else:
                    newSettings[k] = defaultSettings[k][0]

        # if no settings file exists, use the defaults
        else:
            for k in defaultSettings.keys():
                newSettings[k] = defaultSettings[k][0]

        # return the settings dict
        return newSettings

    def populateGUI(self, settings):
        statsChoice = settings['statsChoice']
        if statsChoice == 'Average':
            self.ids.statsChoice_average.state = 'down'
        elif statsChoice == 'Median':
            self.ids.statsChoice_median.state = 'down'
        elif statsChoice == 'Custom':
            self.ids.statsChoice_custom.state = 'down'

    def setStatChoice(self, choice):
        print('choice is {}'.format(choice))
        self.GUI_settings['statsChoice'] = choice

    ### Load Settings Dialog Methods -----------------
    def show_loadSettingsDialog(self):
        # method to pop open the file browser
        content = LoadSettingsDialog(loadSettings=self.loadSettings,
                                    cancelSettings=self.cancelSettings)
        self._popup = Popup(title="Load file", content=content,
                            size_hint=(1, 0.9))
        self._popup.open()


    def loadSettings(self, path, selection):
        # load the selected settings file
        settingsFile = selection[0]

        # read the settings file, override the dict property
        # that has the current settings
        self.GUI_settings = self.readSettings(settingsFile)

        # close settings dialog
        self._popup.dismiss()


    def cancelSettings(self):
        self._popup.dismiss()

    def submitGUI(self):
        """
        method for the GUI submit button.
        Get all setting, save new default settings file
        """
        print(self.GUI_settings)

        ### POSSIBLE TO HAVE ALL OF THIS ACCESSED DIRECTLY FROM GUI_SETTINGS?
        allSettings = {
            'scannerPort': int(self.ids.scannerPort.text),
            'outputPort': int(self.ids.outputPort.text),
            'numTimepts': int(self.ids.numTimepts.text),
            'statsChoice': self.getStatsChoice()
        }

        # write the file
        with open(setupConfigFile, 'w') as outputFile:
            yaml.dump(allSettings, outputFile, default_flow_style=False)


class SetupApp(App):
    """
    Root App class. Calling run method on this class launches
    the GUI
    """
    title = 'Pyneal Setup'
    pass

Factory.register('MainContainer', cls=MainContainer)
Factory.register('LoadSettingsDialog', cls=LoadSettingsDialog)


def launchPynealSetupGUI(settingsFile):
    """
    Launch the pyneal setup GUI. Call this function from the main pyneal.py
    script in order to open the GUI. The GUI will be populated with all of
    the settings specified in the 'settingsFile'.

    settingsFile: path to yaml file containing all of the GUI settings
    """
    # update the global setupConfigFile var with the path passed in
    global setupConfigFile
    setupConfigFile = settingsFile

    # launch the app
    SetupApp().run()


if __name__ == '__main__':
    # specify the settings file to read
    settingsFile = 'setupConfig.yaml'

    # launch setup GUI
    launchPynealSetupGUI(settingsFile)
