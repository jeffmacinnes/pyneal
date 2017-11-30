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

# Path to the setup config file that stores all of the settings
setupConfigFile = 'setupConfig.yaml'


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

        # When the GUI is first created, read the setupConfigFile
        # to get values for all of the settings. If the setupConfigFile
        # doesn't exist, default values will be set
        self.GUI_settings = self.readSettings(setupConfigFile)

        # pass the keywords along to the parent class
        super().__init__(**kwargs)


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
            'test': [True, bool]
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
        # if no settings file, take the defaults
        else:
            for k in defaultSettings.keys():
                newSettings[k] = defaultSettings[k][0]

        # return the settings dict
        return newSettings


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
        print(self.scannerPortInput)
        for i in self.GUI_settings:
            print(self.GUI_settings[i])



class SetupApp(App):
    """
    Root App class. Calling run method on this class launches
    the GUI
    """
    title = 'Pyneal Setup'

    def build(self):
        return MainContainer()
    #
    # def update(self, *args):

    pass


Factory.register('MainContainer', cls=MainContainer)
Factory.register('LoadSettingsDialog', cls=LoadSettingsDialog)



if __name__ == '__main__':
    # run the app
    SetupApp().run()
