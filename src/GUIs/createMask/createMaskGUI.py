""" Create Mask GUI:
GUI to set inputs and option for creating a mask to use during Pyneal real-time
analysis. Pyneal requires that all masks be in subject functional space; this
tool helps create those.

All of the settings are stored in a createMaskConfig.yaml file. This GUI reads
that file to obtain initial settings, and then once the user hits 'submit' the
file is overwritten with new settings

"""

import os
from os.path import join
from pathlib import Path

import wx
import yaml
import nibabel as nib

pynealColor = '#B04555'

class CreateMaskFrame(wx.Frame):
    def __init__(self, parent, title='Create mask', settingsFile=None):
        super(CreateMaskFrame, self).__init__(parent, title=title)

        self.createMaskGUI_dir = os.path.dirname(os.path.abspath(__file__))
        self.pynealDir = str(Path(os.path.abspath(__file__)).resolve().parents[3])
        self.MNI_standardsDir = join(self.pynealDir, 'utils/MNI_templates')
        self.masksDir = join(self.pynealDir, 'utils/masks')

        # initialize all gui panels and settings
        self.settingsFile = settingsFile
        self.InitSettings()
        self.InitUI()

    def InitSettings(self):
        """ Initialize values for all settings """
        defaultSettings = {
            'subjFunc': ['', str],
            'createFuncBrainMask': [True, bool],
            'transformMaskToFunc': [False, bool],
            'subjAnat': ['', str],
            'skullStrip': [True, bool],
            'MNI_standard': [join(self.MNI_standardsDir, 'MNI152_T1_1mm_brain.nii.gz'), str],
            'MNI_mask': ['', str],
            'outputPrefix': ['test', str]
        }

        # initialize dictionary that will eventually hold the new settings
        newSettings = {}

        # load the settingsFile, if it exists and is not empty
        if os.path.isfile(self.settingsFile) and os.path.getsize(self.settingsFile) > 0:
            # open the file, load all settings from the file into a dict
            with open(self.settingsFile, 'r') as ymlFile:
                loadedSettings = yaml.safe_load(ymlFile)

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

        # set the loaded settings dict
        self.GUI_settings = newSettings


    def InitUI(self):
        """ Initialize all GUI windows and widgets """

        # set defaults fonts
        font = self.GetFont()
        font.SetFaceName('Helvetica')
        font.SetPointSize(15)
        self.SetFont(font)
        self.headerFont = wx.Font(wx.FontInfo(20).FaceName('Helvetica').Bold().AntiAliased(True))

        # standard width of entry widgets
        self.pathEntryW = 200

        # create master panel
        self.createMaskPanel = wx.Panel(self, -1)
        self.createMaskPanel.SetBackgroundColour("white")

        # create top level vert sizer that we'll add other sub sizers to
        vbox = wx.BoxSizer(wx.VERTICAL)

        # create sub boxes
        logoSizer = self.createLogoBox()
        funcSizer = self.createFuncBox()
        wholebrainMaskSizer = self.createBrainMaskBox()
        mniMaskSizer = self.createMniMaskBox()
        submitSizer = self.createSubmitBox()

        # add the sizers holding each box to the top level sizer
        vbox.Add(logoSizer, flag=wx.ALL | wx.ALIGN_CENTRE_HORIZONTAL, border=5, proportion=0)
        vbox.Add(funcSizer, flag=wx.EXPAND | wx.ALL, border=5, proportion=0)
        vbox.Add(wx.StaticLine(self.createMaskPanel, -1, size=(380, -1)), flag=wx.ALL | wx.ALIGN_CENTRE_HORIZONTAL, border=10, proportion=0)
        vbox.Add(wholebrainMaskSizer, flag=wx.EXPAND | wx.ALL, border=5, proportion=0)
        vbox.Add(wx.StaticLine(self.createMaskPanel, -1, size=(380, -1)), flag=wx.ALL | wx.ALIGN_CENTRE_HORIZONTAL, border=10, proportion=0)
        vbox.Add(mniMaskSizer, flag=wx.EXPAND | wx.ALL, border=5, proportion=0)
        vbox.Add(wx.StaticLine(self.createMaskPanel, -1, size=(380, -1)), flag=wx.ALL | wx.ALIGN_CENTRE_HORIZONTAL, border=10, proportion=0)
        vbox.Add(submitSizer, flag=wx.EXPAND | wx.ALL, border=10, proportion=0)

        # update appearance of "transform MNI mask..." options
        self.updateTransformMaskOptsVisibility()

        # set the top level sizer to control the master panel
        self.createMaskPanel.SetSizer(vbox)
        vbox.Fit(self)

        # center the frame on the screen
        self.Centre()

    ### (VIEW) -- subbox creation methods -------------------------------------
    def createLogoBox(self):
        """ draw the logo box at top of GUI """
        logoSizer = wx.BoxSizer(wx.HORIZONTAL)

        # add the logo
        logoBMP = wx.Bitmap(join(self.createMaskGUI_dir, 'images/createMaskLogo.bmp'))
        logoImg = wx.StaticBitmap(self.createMaskPanel, -1, logoBMP)

        # add image to sizer for this box
        logoSizer.Add(logoImg, flag=wx.ALIGN_CENTRE_HORIZONTAL | wx.EXPAND, proportion=0)

        return logoSizer

    def createFuncBox(self):
        """ draw the box for inputing the 4D func image """
        funcSizer = wx.GridBagSizer(vgap=5, hgap=5)

        # add text, entry, and change button
        funcLabel = wx.StaticText(self.createMaskPanel, -1,
                                  size=(80,-1),
                                  style=wx.ALIGN_RIGHT,
                                  label='4D FUNC:')
        self.funcEntry = wx.TextCtrl(self.createMaskPanel, -1,
                                size=(self.pathEntryW, -1),
                                style=wx.TE_LEFT,
                                value=self.GUI_settings['subjFunc'])
        self.funcChangeBtn = wx.Button(self.createMaskPanel, -1,
                             size=(70,-1),
                             label='change')
        self.funcChangeBtn.Bind(wx.EVT_BUTTON, self.onChangeFunc)

        # add widgets to sizer
        funcSizer.Add(funcLabel, pos=(0,0), span=(1,1), border=5,
                      flag=wx.ALL)
        funcSizer.Add(self.funcEntry, pos=(0,1), span=(1,2), border=5,
                      flag=wx.EXPAND | wx.ALL)
        funcSizer.Add(self.funcChangeBtn, pos=(0,3), span=(1,1), border=5,
                      flag=wx.ALL)
        funcSizer.AddGrowableCol(1,1)

        return funcSizer

    def createBrainMaskBox(self):
        """ draw the box with checkbox for whole brain mask """
        brainMaskSizer = wx.GridBagSizer(vgap=5, hgap=5)

        # add checkbox and text
        emptySpace = wx.StaticText(self.createMaskPanel, -1, label=" ", size=(100, -1))
        self.brainMaskCheckBox = wx.CheckBox(self.createMaskPanel, -1,
                                 style=wx.CHK_2STATE | wx.ALIGN_RIGHT,
                                 label='Create FUNC whole-brain mask')
        self.brainMaskCheckBox.SetValue(self.GUI_settings['createFuncBrainMask'])
        self.brainMaskCheckBox.Bind(wx.EVT_CHECKBOX, self.onBrainMaskToggled)

        brainMaskSizer.Add(emptySpace, pos=(0,0), span=(1,1), border=5,
                           flag=wx.EXPAND | wx.ALL)
        brainMaskSizer.Add(self.brainMaskCheckBox, pos=(0,1), span=(1,1), border=5,
                         flag=wx.ALIGN_RIGHT | wx.ALL)

        return brainMaskSizer

    def createMniMaskBox(self):
        """ draw box with all settings for MNI mask transformation """
        mniMaskSizer = wx.GridBagSizer(vgap=5, hgap=5)

        # transform mni mask checkbox row
        self.transformMaskCheckBox = wx.CheckBox(self.createMaskPanel, -1,
                                 style=wx.CHK_2STATE | wx.ALIGN_CENTER_HORIZONTAL,
                                 label='Transform MNI mask to FUNC')
        self.transformMaskCheckBox.SetValue(self.GUI_settings['transformMaskToFunc'])
        self.transformMaskCheckBox.Bind(wx.EVT_CHECKBOX, self.onTransformMaskToggled)

        mniMaskSizer.Add(self.transformMaskCheckBox, pos=(0,1), span=(1,1), border=5,
                         flag=wx.ALIGN_CENTER_HORIZONTAL | wx.ALL)

        # hi-res anat input row
        self.anatLabel = wx.StaticText(self.createMaskPanel, -1,
                                  size=(100,-1),
                                  style=wx.ALIGN_RIGHT,
                                  label='hi-res ANAT:')
        self.anatEntry = wx.TextCtrl(self.createMaskPanel, -1,
                                size=(self.pathEntryW, -1),
                                style=wx.TE_LEFT,
                                value=self.GUI_settings['subjFunc'])
        self.anatChangeBtn = wx.Button(self.createMaskPanel, -1,
                             size=(70,-1),
                             label='change')
        self.anatChangeBtn.Bind(wx.EVT_BUTTON, self.onChangeAnat)
        mniMaskSizer.Add(self.anatLabel, pos=(1,0), span=(1,1), border=5,
                      flag=wx.ALL)
        mniMaskSizer.Add(self.anatEntry, pos=(1,1), span=(1,2), border=5,
                      flag=wx.EXPAND | wx.ALL)
        mniMaskSizer.Add(self.anatChangeBtn, pos=(1,3), span=(1,1), border=5,
                      flag=wx.ALL)

        # skull strip row
        self.skullStripCheckBox = wx.CheckBox(self.createMaskPanel, -1,
                                 style=wx.CHK_2STATE)
        self.skullStripCheckBox.SetValue(self.GUI_settings['skullStrip'])
        self.skullStripCheckBox.Bind(wx.EVT_CHECKBOX, self.onSkullStripToggled)

        self.skullStripText = wx.StaticText(self.createMaskPanel, -1,
                                       style=wx.ALIGN_RIGHT,
                                       label='Skull strip?')
        mniMaskSizer.Add(self.skullStripText, pos=(2,1), span=(1,1), border=5,
                         flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT | wx.TOP)
        mniMaskSizer.Add(self.skullStripCheckBox, pos=(2,2), span=(1,1), border=5,
                         flag=wx.ALIGN_CENTER_VERTICAL | wx.ALL)

        # MNI standard row
        self.mniStdLabel = wx.StaticText(self.createMaskPanel, -1,
                                  size=(100,-1),
                                  style=wx.ALIGN_RIGHT,
                                  label='MNI standard:')
        self.mniStdEntry = wx.TextCtrl(self.createMaskPanel, -1,
                                size=(self.pathEntryW, -1),
                                style=wx.TE_LEFT,
                                value=self.GUI_settings['MNI_standard'])
        self.mniStdChangeBtn = wx.Button(self.createMaskPanel, -1,
                             size=(70,-1),
                             label='change')
        self.mniStdChangeBtn.Bind(wx.EVT_BUTTON, self.onChangeMniStd)
        mniMaskSizer.Add(self.mniStdLabel, pos=(3,0), span=(1,1), border=5,
                      flag=wx.ALL)
        mniMaskSizer.Add(self.mniStdEntry, pos=(3,1), span=(1,2), border=5,
                      flag=wx.EXPAND | wx.ALL)
        mniMaskSizer.Add(self.mniStdChangeBtn, pos=(3,3), span=(1,1), border=5,
                      flag=wx.ALL)

        # MNI mask row
        self.mniMaskLabel = wx.StaticText(self.createMaskPanel, -1,
                                  size=(100,-1),
                                  style=wx.ALIGN_RIGHT,
                                  label='MNI mask:')
        self.mniMaskEntry = wx.TextCtrl(self.createMaskPanel, -1,
                                size=(self.pathEntryW, -1),
                                style=wx.TE_LEFT,
                                value=self.GUI_settings['MNI_mask'])
        self.mniMaskChangeBtn = wx.Button(self.createMaskPanel, -1,
                             size=(70,-1),
                             label='change')
        self.mniMaskChangeBtn.Bind(wx.EVT_BUTTON, self.onChangeMniMask)
        mniMaskSizer.Add(self.mniMaskLabel, pos=(4,0), span=(1,1), border=5,
                      flag=wx.ALL)
        mniMaskSizer.Add(self.mniMaskEntry, pos=(4,1), span=(1,2), border=5,
                      flag=wx.EXPAND | wx.ALL)
        mniMaskSizer.Add(self.mniMaskChangeBtn, pos=(4,3), span=(1,1), border=5,
                      flag=wx.ALL)

        # Output prefix row
        self.outputPrefixLabel = wx.StaticText(self.createMaskPanel, -1,
                          size=(100,-1),
                          style=wx.ALIGN_RIGHT,
                          label='Output Prefix:')
        self.outputPrefixEntry = wx.TextCtrl(self.createMaskPanel, -1,
                                size=(180, -1),
                                style=wx.TE_LEFT,
                                value=self.GUI_settings['outputPrefix'])
        mniMaskSizer.Add(self.outputPrefixLabel, pos=(5,0), span=(1,1), border=5,
                      flag=wx.ALL)
        mniMaskSizer.Add(self.outputPrefixEntry, pos=(5,1), span=(1,2), border=5,
                      flag=wx.ALL)

        # add widgets to sizer
        mniMaskSizer.AddGrowableCol(1,1)

        return mniMaskSizer

    def createSubmitBox(self):
        """ create the submit button box """
        submitSizer = wx.BoxSizer(wx.VERTICAL)

        # divider
        bmp = wx.Bitmap(join(self.createMaskGUI_dir, 'images/headerThin.bmp'))
        headerImg = wx.StaticBitmap(self.createMaskPanel, -1, bmp)
        submitSizer.Add(headerImg, proportion=0,
                        flag=wx.ALIGN_CENTRE_HORIZONTAL | wx.TOP)

        btnSize = (200, 20)
        submitBtn = wx.Button(self.createMaskPanel, -1,
                              label='Submit',
                              size=btnSize)
        submitBtn.Bind(wx.EVT_BUTTON, self.onSubmit)

        submitSizer.Add(submitBtn, proportion=0, border=5,
                           flag=wx.ALIGN_CENTRE_HORIZONTAL | wx.ALL)

        return submitSizer

    ### (CONTROL) -- Event Handling and User Interaction ----------------------
    def onChangeFunc(self, e):
        """ open a file dialog for selecting the input 4D func file """
        # get current value from GUI
        currentFunc = self.funcEntry.GetValue()
        if os.path.exists(currentFunc):
            startDir = os.path.split(currentFunc)[0]
        else:
            startDir = self.pynealDir
        wildcard = '*.gz'
        funcPath = self.openFileDlg(msg="Choose a 4D func nifti (.nii.gz) to use as reference",
                                    wildcard=wildcard,
                                    startDir=startDir)
        # update widgets
        if funcPath is not None:
            if funcPath != self.GUI_settings['subjFunc']:
                # set the new path
                self.GUI_settings['subjFunc'] = funcPath
                self.funcEntry.SetValue(self.GUI_settings['subjFunc'])

    def onBrainMaskToggled(self, e):
        self.GUI_settings['createFuncBrainMask'] = self.brainMaskCheckBox.GetValue()

    def onTransformMaskToggled(self, e):
        self.GUI_settings['transformMaskToFunc'] = self.transformMaskCheckBox.GetValue()

        # update appearance of transform mni mask options
        self.updateTransformMaskOptsVisibility()

    def onChangeAnat(self, e):
        """ open a file dialog for selecting the hi-res ANAT file """
        # get current value from GUI
        currentAnat = self.anatEntry.GetValue()
        if os.path.exists(currentAnat):
            startDir = os.path.split(currentAnat)[0]
        else:
            startDir = self.pynealDir
        wildcard = '*.gz'
        anatPath = self.openFileDlg(msg="Choose hi-res ANAT (.nii.gz) for this subject",
                                    wildcard=wildcard,
                                    startDir=startDir)
        # update widgets
        if anatPath is not None:
            if anatPath != self.GUI_settings['subjAnat']:
                # set the new path
                self.GUI_settings['subjAnat'] = anatPath
                self.anatEntry.SetValue(self.GUI_settings['subjAnat'])

    def onSkullStripToggled(self, e):
        self.GUI_settings['skullStrip'] = self.skullStripCheckBox.GetValue()

    def onChangeMniStd(self, e):
        """ open a file dialog for selecting new MNI standard """
        # get current value from GUI
        currentMniStd = self.mniStdEntry.GetValue()
        if os.path.exists(currentMniStd):
            startDir = os.path.split(currentMniStd)[0]
        else:
            startDir = self.MNI_standardsDir
        wildcard = '*.gz'
        mniStdPath = self.openFileDlg(msg="Choose the MNI standard (.nii.gz) with same dims/orientation as mask",
                                    wildcard=wildcard,
                                    startDir=startDir)
        # update widgets
        if mniStdPath is not None:
            if mniStdPath != self.GUI_settings['MNI_standard']:
                # set the new mask path
                self.GUI_settings['MNI_standard'] = mniStdPath
                self.mniStdEntry.SetValue(self.GUI_settings['MNI_standard'])

    def onChangeMniMask(self, e):
        """ open a file dialog for selecting new MNI mask """
        # get current value from GUI
        currentMniMask = self.mniMaskEntry.GetValue()
        if os.path.exists(currentMniMask):
            startDir = os.path.split(currentMniMask)[0]
        else:
            startDir = self.masksDir
        wildcard = '*.gz'
        maskPath = self.openFileDlg(msg="Choose the MNI-space mask (.nii.gz)",
                                    wildcard=wildcard,
                                    startDir=startDir)
        # update widgets
        if maskPath is not None:
            if maskPath != self.GUI_settings['MNI_mask']:
                # set the new mask path
                self.GUI_settings['MNI_mask'] = maskPath
                self.mniMaskEntry.SetValue(self.GUI_settings['MNI_mask'])

    def onSubmit(self, e):
        """ update and confirm all settings and submit """
        # get all settings from GUI
        self.getAllSettings()

        errorCheckPassed = self.check_GUI_settings()
        # write GUI settings to file
        if errorCheckPassed:
            # write the settings as the new config yaml file
            with open(self.settingsFile, 'w') as outputFile:
                yaml.dump(self.GUI_settings, outputFile, default_flow_style=False)

        # close
        self.Close()

    def openFileDlg(self, msg="Choose file", wildcard='', startDir=''):
        """ Open file dialog """
        dlg = wx.FileDialog(self, message=msg,
                            defaultDir=startDir,
                            defaultFile="",
                            wildcard="({})|{}".format(wildcard, wildcard),
                            style=wx.FD_OPEN)
        # return selected file
        selectedPath = None
        if dlg.ShowModal() == wx.ID_OK:
            path = dlg.GetPath()
            selectedPath = path
        dlg.Destroy()
        return selectedPath

    def showMessageDlg(self, msg, title, style):
        """show pop up message dialog"""
        dlg = wx.MessageDialog(parent=None, message=msg,
                               caption=title, style=style)
        dlg.ShowModal()
        dlg.Destroy()

    ### (MISC) - HELPER FUNCTIONS ---------------------------------------------
    def updateTransformMaskOptsVisibility(self):
        """ set the visibility of options under the transform mask box based
        on checkbox value
        """
        for widget in [self.anatLabel, self.anatEntry, self.anatChangeBtn,
                    self.skullStripText, self.skullStripCheckBox,
                    self.mniStdLabel, self.mniStdEntry, self.mniStdChangeBtn,
                    self.mniMaskLabel, self.mniMaskEntry, self.mniMaskChangeBtn,
                    self.outputPrefixLabel, self.outputPrefixEntry]:
            if self.GUI_settings['transformMaskToFunc']:
                widget.Enable()
            else:
                widget.Disable()

    def check_GUI_settings(self):
        """ Check the validity of all current GUI settings

        Returns
        -------
        errorCheckPassed : Boolean
            True/False flag indicating whether ALL of the current settings are
            valid or not

        """
        errorMsg = []

        # check if paths are valid
        for p in ['subjFunc', 'subjAnat', 'MNI_standard', 'MNI_mask']:
            try:
                os.path.isfile(self.GUI_settings[p])
            except:
                errorMsg.append('{}: not a valid path'.format(k))

        # show the error notification, if any
        if len(errorMsg) > 0:
            self.showMessageDlg('\n'.join(errorMsg), 'Settings Error', wx.YES_DEFAULT | wx.ICON_EXCLAMATION)
            errorCheckPassed = False
        else:
            errorCheckPassed = True
        return errorCheckPassed

    def getAllSettings(self):
        """ get all values from the GUI and write into the GUI_settings dict"""
        self.GUI_settings['subjFunc'] = self.funcEntry.GetValue()
        self.GUI_settings['createFuncBrainMask'] = self.brainMaskCheckBox.GetValue()
        self.GUI_settings['transformMaskToFunc'] = self.transformMaskCheckBox.GetValue()
        self.GUI_settings['subjAnat'] = self.anatEntry.GetValue()
        self.GUI_settings['skullStrip'] = self.skullStripCheckBox.GetValue()
        self.GUI_settings['MNI_standard'] = self.mniStdEntry.GetValue()
        self.GUI_settings['MNI_mask'] = self.mniMaskEntry.GetValue()
        self.GUI_settings['outputPrefix'] = self.outputPrefixEntry.GetValue()




class CreateMaskApp(wx.App):
    """ Application class for setup GUI """
    def __init__(self, settingsFile):
        self.settingsFile = settingsFile  # create local reference to settingsFile

        super().__init__() # initialize the parent wx.App class

    def OnInit(self):
        self.frame = CreateMaskFrame(None,
                                     title='Create Mask',
                                     settingsFile=self.settingsFile)
        self.frame.Show()
        self.SetTopWindow(self.frame)
        return True


def launchCreateMaskGUI(settingsFile):
    app = CreateMaskApp(settingsFile)
    app.MainLoop()

if __name__ == '__main__':
    # specify create mask settings file to read
    settingsFile = 'createMaskConfig.yaml'

    # launch create mask GUI
    launchCreateMaskGUI(settingsFile)
