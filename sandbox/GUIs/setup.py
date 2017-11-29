import os
import sys

import yaml

from kivy.app import App
from kivy.uix.widget import Widget
from kivy.uix.boxlayout import BoxLayout
from kivy.properties import StringProperty, ObjectProperty
from kivy.storage.jsonstore import JsonStore
from kivy.uix.filechooser import FileChooserListView
from kivy.uix.popup import Popup
from kivy.factory import Factory

# Set Window Size
from kivy.config import Config
Config.set('graphics', 'width', '400')
Config.set('graphics', 'height', '700')

class LoadSettingsDialog(BoxLayout):
    loadSettings = ObjectProperty(None)
    cancelSettings = ObjectProperty(None)


class MainContainer(BoxLayout):
    """
    Custom widget that is the root level container for all
    other widgets
    """
    # create properties for all of the settings
    scannerPort_setting = ObjectProperty('')
    outputPort_setting = ObjectProperty('')
    numTimepts_setting = ObjectProperty('')

    def __init__(self, **kwargs):
        super(MainContainer, self).__init__(**kwargs)

        # Read settings file upon first initialization
        self.settings = self.readSettings('setupConfig.yaml')

        # Populate GUI with these settings
        self.populate_settings(self.settings)


    def readSettings(self, settingsFile):
        """
        Look for the setupConfig.yaml file, and if it exists, overwrite
        the default settings.
        If it doesn't exist, create it with default values.
        Return a dict with all settings
        """
        # set up defaults. Store the value and the dtype. This is used
        # to confirm that a loaded setting is valid
        defaultSettings ={
            'scannerPort': [999, int],
            'outputPort': [999, int],
            'numTimepts': [999, int]
            }

        # initialize dictionary that will eventually hold all of the settings
        settings = {}

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
                        settings[k] = loadedValue
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
                    settings[k] = defaultSettings[k][0]
        # if no settings file, take the defaults
        else:
            for k in defaultSettings.keys():
                settings[k] = defaultSettings[k][0]

        # return the settings dict
        return settings


    def populate_settings(self, settings):
        """
        set all of the GUI values based on the settings dict
        """
        self.scannerPort_setting = str(settings['scannerPort'])
        self.outputPort_setting = str(settings['outputPort'])
        self.numTimepts_setting = str(settings['numTimepts'])


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

        # read the settings file, return dict
        self.settings = self.readSettings(settingsFile)

        # populate the GUI with the loaded settings
        self.populate_settings(self.settings)

        # close settings dialog
        self._popup.dismiss()

    def cancelSettings(self):
        self._popup.dismiss()



class SetupApp(App):
    """
    Root App class. Calling run method on this class launches
    the GUI
    """
    title = 'Pyneal Setup'

    pass
    # def build(self):
    #     return MainContainer()


Factory.register('MainContainer', cls=MainContainer)
Factory.register('LoadSettingsDialog', cls=LoadSettingsDialog)



if __name__ == '__main__':
    # run the app
    SetupApp().run()
