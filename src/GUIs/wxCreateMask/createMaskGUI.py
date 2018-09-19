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
        self.pynealDir = Path(os.path.abspath(__file__)).resolve().parents[3]

        # initialize all gui panels and settings
        self.InitSettings()
        self.InitUI()

    def InitSettings(self):
        self.GUI_settings = {
            'subjFunc': '/Users/jeff',
            'createFuncBrainMask': True,
            'transformMaskToFunc': True,
            'subjAnat': '/Users/jeff/anat',
            'skullStrip': True,
            'MNI_standard': '/Users/jeff/MNI_standard',
            'MNI_mask': '/Users/jeff/MNI_mask',
            'outputPrefix': 'test'
        }

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
                                 style=wx.CHK_2STATE | wx.ALIGN_RIGHT,
                                 label='Transform MNI mask to FUNC')
        self.transformMaskCheckBox.SetValue(self.GUI_settings['transformMaskToFunc'])
        self.transformMaskCheckBox.Bind(wx.EVT_CHECKBOX, self.onTransformMaskToggled)

        mniMaskSizer.Add(self.transformMaskCheckBox, pos=(0,1), span=(1,1), border=5,
                         flag=wx.ALIGN_RIGHT | wx.ALL)

        # hi-res anat input row
        anatLabel = wx.StaticText(self.createMaskPanel, -1,
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
        mniMaskSizer.Add(anatLabel, pos=(1,0), span=(1,1), border=5,
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

        skullStripText = wx.StaticText(self.createMaskPanel, -1,
                                       style=wx.ALIGN_RIGHT,
                                       label='Skull strip?')
        mniMaskSizer.Add(skullStripText, pos=(2,1), span=(1,1), border=5,
                         flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT | wx.TOP)
        mniMaskSizer.Add(self.skullStripCheckBox, pos=(2,2), span=(1,1), border=5,
                         flag=wx.ALIGN_CENTER_VERTICAL | wx.ALL)

        # MNI standard row
        mniStdLabel = wx.StaticText(self.createMaskPanel, -1,
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
        mniMaskSizer.Add(mniStdLabel, pos=(3,0), span=(1,1), border=5,
                      flag=wx.ALL)
        mniMaskSizer.Add(self.mniStdEntry, pos=(3,1), span=(1,2), border=5,
                      flag=wx.EXPAND | wx.ALL)
        mniMaskSizer.Add(self.mniStdChangeBtn, pos=(3,3), span=(1,1), border=5,
                      flag=wx.ALL)

        # MNI mask row
        mniMaskLabel = wx.StaticText(self.createMaskPanel, -1,
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
        mniMaskSizer.Add(mniMaskLabel, pos=(4,0), span=(1,1), border=5,
                      flag=wx.ALL)
        mniMaskSizer.Add(self.mniMaskEntry, pos=(4,1), span=(1,2), border=5,
                      flag=wx.EXPAND | wx.ALL)
        mniMaskSizer.Add(self.mniMaskChangeBtn, pos=(4,3), span=(1,1), border=5,
                      flag=wx.ALL)

        # Output prefix row
        outputPrefixLabel = wx.StaticText(self.createMaskPanel, -1,
                          size=(100,-1),
                          style=wx.ALIGN_RIGHT,
                          label='Output Prefix:')
        self.outputPrefixEntry = wx.TextCtrl(self.createMaskPanel, -1,
                                size=(180, -1),
                                style=wx.TE_LEFT,
                                value=self.GUI_settings['outputPrefix'])
        mniMaskSizer.Add(outputPrefixLabel, pos=(5,0), span=(1,1), border=5,
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
        wildcard = '*.gz'
        startDir = os.path.split(self.GUI_settings['subjFunc'])[0]
        funcPath = self.openFileDlg(msg="Choose a 4D func nifti (.nii.gz) to use as reference",
                                    wildcard=wildcard,
                                    startDir=startDir)

        # update widgets
        if funcPath is not None:
            if funcPath != self.GUI_settings['subjFunc']:
                # set the new mask path
                self.GUI_settings['subjFunc'] = funcPath
                self.maskPathEntry.SetValue(self.GUI_settings['subjFunc'])

    def onBrainMaskToggled(self, e):
        print('clicking the brain mask checkbox')

    def onTransformMaskToggled(self, e):
        print('clicking the transform mni mask to func checkbox')

    def onChangeAnat(self, e):
        print('changing the subj anat path')

    def onSkullStripToggled(self, e):
        print('clicking the skull strip checkbox')

    def onChangeMniStd(self, e):
        print('changing the MNI standard selection')

    def onChangeMniMask(self, e):
        print('changing the MNI mask selection')

    def onSubmit(self, e):
        print('submit button pressed')

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
