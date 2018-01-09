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
import re

import yaml

from kivy.app import App
from kivy.uix.widget import Widget
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.boxlayout import BoxLayout
from kivy.properties import StringProperty, NumericProperty, ListProperty, ObjectProperty, DictProperty
from kivy.uix.filechooser import FileChooserListView
from kivy.uix.popup import Popup
from kivy.factory import Factory

# Set Window Size
from kivy.config import Config
Config.set('graphics', 'width', '400')
Config.set('graphics', 'height', '700')

# initialize global var that will store path to the setupConfigFile
setupConfigFile = None

class SectionHeading(BoxLayout):
    textWidth = NumericProperty()
    labelText = StringProperty('test')


class NumberInputField(TextInput):
    # restrict the number fields to 0-9 input only
    pat = re.compile('[^0-9]')
    def insert_text(self, substring, from_undo=False):
        pat = self.pat
        s = re.sub(pat, '', substring)
        return super().insert_text(s, from_undo=from_undo)


class LoadFileDialog(BoxLayout):
    """ generic class to present file chooser popup """
    loadFunc= ObjectProperty(None)
    cancelFileChooser = ObjectProperty(None)
    path = StringProperty()
    fileFilter = ListProperty()


class ErrorNotification(BoxLayout):
    """ class to load error notification popup """
    errorMsg = StringProperty('')


class MainContainer(BoxLayout):
    """
    Root level widget for the setup GUI
    """
    # create a kivy DictProperty that will store a dictionary with all of the
    # settings for the GUI.
    GUI_settings = DictProperty({}, rebind=True)
    textColor = ListProperty([0,0,0,1])
    analysisInfo = StringProperty('')

    def __init__(self, **kwargs):
        self.GUI_settings = self.readSettings(setupConfigFile)

        self.setAnalysisInfo()

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
            'maskFile': ['None', str],
            'maskIsWeighted': [True, bool],
            'numTimepts': [999, int],
            'analysisChoice': ['Average', str]
            }

        # initialize dictionary that will eventually hold the new settings
        newSettings = {}

        # load the settingsFile, if it exists and is not empty
        if os.path.isfile(settingsFile) and os.path.getsize(settingsFile) > 0:
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


    def setMaskIsWeighted(self):
        print(self.ids.maskIsWeighted.active)
        self.GUI_settings['maskIsWeighted'] = self.ids.maskIsWeighted.active
        self.setAnalysisInfo()


    def setAnalysisChoice(self, choice):
        self.GUI_settings['analysisChoice'] = choice
        self.setAnalysisInfo()


    def setAnalysisInfo(self):
        """
        Update the info on the analysis section
        """
        if self.GUI_settings['analysisChoice'] in ['Average', 'Median']:
            if self.GUI_settings['maskIsWeighted']:
                self.analysisInfo = 'Compute the Weighted {} of voxels within mask'.format(self.GUI_settings['analysisChoice'])
            else:
                self.analysisInfo = 'Compute the {} of voxels within mask'.format(self.GUI_settings['analysisChoice'])
        elif self.GUI_settings['analysisChoice'] == 'Custom':
            self.analysisInfo = 'Custom Analysis: {}'.format(split(self.GUI_settings.analysisChoice)[1])


    def check_GUI_settings(self):
        """
        Examine the GUI_settings dict to make sure everything is valid
        """
        errorMsg = []
        # check if text inputs are valid integers
        for k in ['scannerPort', 'outputPort', 'numTimepts']:
            try:
                tmp = int(self.GUI_settings[k])
            except:
                errorMsg.append('{}: not an integer'.format(k))
                pass

        # check if maskFile is a valid path
        if not os.path.isfile(self.GUI_settings['maskFile']):
            errorMsg.append('{} is not a valid mask file'.format(self.GUI_settings['maskFile']))

        # show the error notification, if any
        if len(errorMsg) > 0:
            self.show_ErrorNotification('\n\n'.join(errorMsg))
            errorCheckPassed = False
        else:
            errorCheckPassed = True
        return errorCheckPassed


    def submitGUI(self):
        """
        method for the GUI submit button. Get all setting, confirm they
        are valid, and save new settings file
        """
        ## Error Check All GUI SETTINGS
        errorCheckPassed = self.check_GUI_settings()

        # write GUI settings to file
        if errorCheckPassed:
            # Convery the GUI_settings from kivy dictproperty to a regular ol'
            # python dict (and do some reformatting along the way)
            allSettings = {}
            for k in self.GUI_settings.keys():
                # convert text inputs to integers
                if k in ['scannerPort', 'outputPort', 'numTimepts']:
                        allSettings[k] = int(self.GUI_settings[k])
                else:
                    allSettings[k] = self.GUI_settings[k]

            # write the settings as the new config yaml file
            with open(setupConfigFile, 'w') as outputFile:
                yaml.dump(allSettings, outputFile, default_flow_style=False)


    ### File Chooser Dialog Methods ###########################################
    def show_loadFileDialog(self, path='~/', fileFilter=[], loadFunc=None):
        """
        generic function to present a popup window that will allow users
        to select a file. Customize this with the parameters you pass in
            - path: path where the file browswer will start
            - fileFilter: list of file types to filter; e.g. ['*.txt']
            - loadFunc: function that will be called when 'load' button pressed
        """
        # method to pop open a file browser
        content = LoadFileDialog(loadFunc=loadFunc,
                                    cancelFileChooser=self.cancelFileChooser,
                                    path=path,
                                    fileFilter=fileFilter)
        self._popup = Popup(title="Load File", content=content,
                            size_hint=(0.9,0.9))
        self._popup.open()


    def cancelFileChooser(self):
        # close the file chooser dialog
        self._popup.dismiss()


    ### Custom functions for different load button behaviors ------------------
    def loadSettings(self, path, selection):
        # called by the load button on settings file selection dialog
        if len(selection) > 0:
            # read the settings file, load new settings into GUI
            settingsFile = selection[0]
            self.GUI_settings = self.readSettings(settingsFile)

        # close  dialog
        self._popup.dismiss()


    def loadMask(self, path, selection):
        # called by load button on mask selection dialog
        if len(selection) > 0:
            # Store maskFile in the GUI settings dict
            maskFile = selection[0]
            self.GUI_settings['maskFile'] = maskFile

        # close dialog
        self._popup.dismiss()


    def loadCustomAnalysis(self, path, selection):
        # called by load button on custom analysis selection dialog
        if len(selection) > 0:
            # Store custom stat file in the GUI settings dict
            customStatFile = selection[0]
            self.GUI_settings['analysisChoice'] = customStatFile
            self.setAnalysisInfo()

            # close dialog
            self._popup.dismiss()


    ### Show Notification Pop-up ##############################################
    def show_ErrorNotification(self, msg):
        self._notification = Popup(
                        title='Errors',
                        content=ErrorNotification(errorMsg=msg),
                        size_hint=(.5, .5)).open()


class SetupApp(App):
    """
    Root App class. This will look for the setup.kv file in the same
    directory and build the GUI according to the parameters outlined in
    that file. Calling 'run' on this class instance will launch the GUI
    """
    title = 'Pyneal Setup'
    pass


# Register the various components of the GUI
Factory.register('MainContainer', cls=MainContainer)
Factory.register('LoadFileDialog', cls=LoadFileDialog)
Factory.register('ErrorNotification', cls=ErrorNotification)

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


# For testing purposes, you can call this GUI directly from the
# command line
if __name__ == '__main__':
    # specify the settings file to read
    settingsFile = '../setupConfig.yaml'

    # launch setup GUI
    launchPynealSetupGUI(settingsFile)
