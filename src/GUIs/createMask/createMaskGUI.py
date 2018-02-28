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
from os.path import join, dirname, exists
import sys

import yaml

from kivy.app import App
from kivy.uix.widget import Widget
from kivy.uix.label import Label
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.textinput import TextInput
from kivy.properties import StringProperty, NumericProperty, ListProperty, ObjectProperty, DictProperty, BooleanProperty
from kivy.uix.filechooser import FileChooserListView
from kivy.uix.popup import Popup
from kivy.factory import Factory

# Set Window Size
from kivy.config import Config
Config.set('graphics', 'width', '450')
Config.set('graphics', 'height', '600')

# initialize global var that will store path to createMaskConfig.yaml file
createMaskConfigFile = None

# global paths
setupGUI_dir = os.path.dirname(os.path.abspath(__file__))
pynealDir = dirname(dirname(dirname(setupGUI_dir)))

submitButtonPressed = False


class FilePathInputField(TextInput):
    pass


class InputPathWidget(BoxLayout):
    """
    class for allowing user to modify a file path. Contains a
    text input field showing the current path, which can be modified by hand.
    Alternatively, the user can click the folder icon to open up a file browser
    to select a new file/dir using that method
    """
    setupGUI_dir = os.path.dirname(os.path.abspath(__file__))
    textColor = ListProperty([0,0,0,1])
    disabledTextColor = ListProperty([.6, .6, .6, 1])
    labelText = StringProperty('test')
    currentPath = StringProperty()
    isDisabled = BooleanProperty(False)

    def updateCurrentPath(self, path, selection):
        # if a file was selected, return full path to the file
        if len(selection) > 0:
            self.currentPath = join(path, selection[0])
        # if it was a dir instead, just return the path to the dir
        else:
            self.currentPath = path

        # close the parent popup
        self._popup.dismiss()


    def launchFileBrowser(self, path='~/', fileFilter=[]):
        """
        generic function to present a popup window with a file browser. Customize this with the parameters you pass in
            - path: path where the file browser will start
            - fileFilter: list of file types to filter; e.g. ['*.txt']
            - loadFunc: function that will be called when 'load' button pressed
        """
        # check to make sure the current path points to a real location
        if os.path.exists(self.currentPath):
            startingPath = self.currentPath
        else:
            startingPath = '~/'
        print(startingPath)
        # method to pop open a file browser
        content = LoadFileDialog(loadFunc=self.updateCurrentPath,
                                    cancelFileChooser=self.cancelFileChooser,
                                    path=startingPath,
                                    fileFilter=fileFilter)
        self._popup = Popup(title="Select", content=content,
                            size_hint=(0.9,0.9))
        self._popup.open()


    def cancelFileChooser(self):
        # close the file chooser dialog
        self._popup.dismiss()


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
    Root level widget for the createMask GUI
    """
    # create a kivy DictProperty that will store a dictionary with all of the
    # settings for the GUI.
    GUI_settings = DictProperty({}, rebind=True)
    setupGUI_dir = os.path.dirname(os.path.abspath(__file__))
    MNI_standards_dir = join(pynealDir, 'utils/MNI_templates')

    textColor = ListProperty([0,0,0,1])
    disabledTextColor = ListProperty([.6, .6, .6, 1])

    def __init__(self, **kwargs):
        self.GUI_settings = self.readSettings(createMaskConfigFile)

        # pass the keywords along to the parent class
        super().__init__(**kwargs)


    ### Methods for dealing with loading/saving Settings -----------------------
    def readSettings(self, settingsFile):
        """
        Open the supplied settingsFile, and compare to the default
        values. Any valid setting in the settingsFile will override
        the default
        """
        # set up defaults
        defaultSettings = {
            'subjFunc': ['', str],
            'createFuncBrainMask': [True, bool],
            'transformMaskToFunc': [False, bool],
            'subjAnat': ['', str],
            'MNI_standard': [join(self.MNI_standards_dir, 'MNI152_T1_1mm_brain.nii.gz'), str],
            'MNI_mask': ['', str],
            'outputPrefix': ['test', str]
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


    def setCreateFuncBrainMask(self):
        self.GUI_settings['createFuncBrainMask'] = self.ids.createFuncBrainMaskCheckbox.active


    def setTransformMaskToFunc(self):
        self.GUI_settings['transformMaskToFunc'] = self.ids.transformMaskToFuncCheckbox.active


    def submitGUI(self):
        """
        Get all settings, confirm they are valid, save new settings file
        """
        # Error check all GUI settings
        errorCheckPassed = self.check_GUI_settings()

        # write GUI settings to file
        if errorCheckPassed:
            # Convery the GUI_settings from kivy dictproperty to a regular ol'
            # python dict
            allSettings = {}
            for k in self.GUI_settings.keys():
                allSettings[k] = self.GUI_settings[k]

            # write the settings as the new config yaml file
            with open(createMaskConfigFile, 'w') as outputFile:
                yaml.dump(allSettings, outputFile, default_flow_style=False)

            # Close the GUI
            global submitButtonPressed
            submitButtonPressed = True
            App.get_running_app().stop()


    def check_GUI_settings(self):
        """
        Make sure all of the GUI settings are legit
        """
        errorMsg = []

        ### check if input 4D func is valid
        subjFuncInput = self.ids.subjFuncWidget.currentPath
        if exists(subjFuncInput):
            self.GUI_settings['subjFunc'] = subjFuncInput
        else:
            errorMsg.append('4D FUNC path not valid: {}'.format(subjFuncInput))

        ## make sure at least one checkbox is selected
        self.GUI_settings['createFuncBrainMask'] = self.ids.createFuncBrainMaskCheckbox.active
        self.GUI_settings['transformMaskToFunc'] = self.ids.transformMaskToFuncCheckbox.active
        if not any([(self.GUI_settings['transformMaskToFunc']),
                    (self.GUI_settings['createFuncBrainMask'])]):
            errorMsg.append('Must check at least one mask option')

        ### check if hi-res anat is valid
        subjAnatInput = self.ids.subjAnatWidget.currentPath
        if exists(subjAnatInput):
            self.GUI_settings['subjAnat'] = subjAnatInput
        else:
            errorMsg.append('hi-res ANAT path not valid: {}'.format(subjAnatInput))

        ### check if MNI_standard is valid
        MNI_standardInput = self.ids.MNI_standardWidget.currentPath
        if exists(MNI_standardInput):
            self.GUI_settings['MNI_standard'] = MNI_standardInput
        else:
            errorMsg.append('MNI standard path not valid: {}'.format(MNI_standardInput))

        ### check if MNI_mask is valid
        MNI_maskInput = self.ids.MNI_maskWidget.currentPath
        if exists(MNI_maskInput):
            self.GUI_settings['MNI_mask'] = MNI_maskInput
        else:
            errorMsg.append('MNI mask path not valid: {}'.format(MNI_maskInput))

        ### Check if outputPrefix is specified, remove any spaces
        outputPrefixInput = self.ids.outputPrefixWidget.text
        if len(outputPrefixInput) > 0:
            self.GUI_settings['outputPrefix'] = outputPrefixInput.replace(' ', '')
        else:
            errorMsg.append('Output prefix not specified')

        # show the error notification, if any
        if len(errorMsg) > 0:
            self.show_ErrorNotification('\n\n'.join(errorMsg))
            errorCheckPassed = False
        else:
            errorCheckPassed = True

        return errorCheckPassed


    ### Show Notification Pop-up ##############################################
    def show_ErrorNotification(self, msg):
        self._notification = Popup(
                        title='Errors',
                        content=ErrorNotification(errorMsg=msg),
                        size_hint=(.5, .5)).open()


class CreateMaskGUIApp(App):
    """
    Root App class. This will look for the createMaskGUI.kv file in the same
    directory and build the GUI according to the parameters outlined in that file.
    Calling 'run' on this class instance will launch the GUI
    """
    title = 'Create Mask'

    def on_stop(self):
        global submitButtonPressed
        if not submitButtonPressed:
            sys.exit()

# Register the various components of the GUI
Factory.register('MainContainer', cls=MainContainer)
Factory.register('LoadFileDialog', cls=LoadFileDialog)
Factory.register('ErrorNotification', cls=ErrorNotification)
Factory.register('InputPathWidget', cls=InputPathWidget)


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
