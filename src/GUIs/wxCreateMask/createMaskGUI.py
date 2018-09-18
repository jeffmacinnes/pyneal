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
            'subjFunc': '/Users/jeff'
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

        # add the sizers holding each box to the top level sizer
        vbox.Add(logoSizer, flag=wx.ALL | wx.ALIGN_CENTRE_HORIZONTAL, border=5, proportion=0)
        vbox.Add(funcSizer, flag=wx.EXPAND | wx.ALL, border=5, proportion=0)

        #sl = wx.StaticLine(self.createMaskPanel, -1)
        vbox.Add(wx.StaticLine(self.createMaskPanel, -1, size=(380, -1)), flag=wx.ALL | wx.ALIGN_CENTRE_HORIZONTAL, border=10, proportion=0)

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
        changeBtn = wx.Button(self.createMaskPanel, -1,
                             size=(80,-1),
                             label='change')
        changeBtn.Bind(wx.EVT_BUTTON, self.onChangeFunc)

        # add widgets to sizer
        funcSizer.Add(funcLabel, pos=(1,0), span=(1,1), border=5,
                      flag=wx.ALL)
        funcSizer.Add(self.funcEntry, pos=(1,1), span=(1,2), border=5,
                      flag=wx.EXPAND | wx.ALL)
        funcSizer.Add(changeBtn, pos=(1,3), span=(1,1), border=5,
                      flag=wx.EXPAND)
        funcSizer.AddGrowableCol(1,1)

        return funcSizer

    ### (CONTROL) -- Event Handling and User Interaction ----------------------
    def onChangeFunc(self, e):
        print('changing the subj func path')


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
