""" Pyneal Setup GUI:

Pyneal is configured using settings stored in a setupConfig.yaml file in
pyneal/src/GUIs/pynealSetup. This setup GUI is basically just a way to view the
current settings as specified by that file, as well as a convienient way for
users to update those settings to fit the parameters of a particular
experiment.

When Pyneal is launched, it'll first open this GUI and give users a chance to
verify/change the current settings. When the user hits 'Submit', the settings
from the GUI will be re-written to the setupConfig.yaml file, and subsequent
stages of Pyneal will read from that file.

Users should not need to edit the setupConfig.yaml file directly. Instead, they
can make a custom .yaml file with any of the Pyneal settings they wish to
specify, and load that file from within the GUI. Any setting specified by this
file will overwrite the current GUI value; all other settings will be taken
from the setupConfig.yaml file. This is a way for users to keep unique settings
files for different experiments.

"""

import os
from os.path import join

import wx
import yaml
import nibabel as nib

pynealColor = '#B04555'


class SetupFrame(wx.Frame):
    def __init__(self, parent, title="Pyneal Setup", settingsFile=None):
        super(SetupFrame, self).__init__(parent, title=title)  #initialize the parent class
        self.setupGUI_dir = os.path.dirname(os.path.abspath(__file__))

        # initialize all gui panels and settings
        self.settingsFile = settingsFile
        self.InitSettings()
        self.InitUI()

    def InitSettings(self):
        """ Initialize values for all settings """
        defaultSettings = {
            'pynealHost': ['127.0.0.1', str],
            'pynealScannerPort': [999, int],
            'resultsServerPort': [999, int],
            'maskFile': ['None', str],
            'maskIsWeighted': [True, bool],
            'numTimepts': [999, int],
            'analysisChoice': ['Average', str],
            'outputPath': ['', str],
            'launchDashboard': [True, bool],
            'dashboardPort': [5557, int],
            'dashboardClientPort': [5558, int]}

        # initialize the dict that will hold the new settings
        newSettings = {}

        # load the settingsFile, if it exists and is not empty
        if os.path.isfile(self.settingsFile) and os.path.getsize(self.settingsFile) > 0:
            # open the file, load all settings from the file into a dict
            with open(settingsFile, 'r') as ymlFile:
                loadedSettings = yaml.load(ymlFile)

            # loop over all default settings and see if there is a loaded setting
            # that should overwrite the default
            for k in defaultSettings.keys():
                # does this key exist in loaded settings?
                if k in loadedSettings.keys():
                    loadedValue = loadedSettings[k]

                    # make sure loaded setting has correct dtype before loading into GUI
                    if type(loadedValue) == defaultSettings[k][1]:
                        newSettings[k] = loadedValue
                    else:
                        # print warning
                        print('Problem loading the settings file!')
                        print('{} setting expecting dtype {}, but got {}. Using default instead'.format(
                              k,
                              defaultSettings[k][1],
                              type(loadedValue)))
                        newSettings[k] = defaultSettings[k][0]
                # otherwise take defaule
                else:
                    newSettings[k] = defaultSettings[k][0]

        # if no settings file exists, use defaults
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

        # create master panel
        self.setupPanel = wx.Panel(self, -1)
        self.setupPanel.SetBackgroundColour("white")

        # create top level sizer that we will add all boxes to
        vbox = wx.BoxSizer(wx.VERTICAL)

        # create the panels
        logoSizer = self.createLogoBox()
        commSizer = self.createCommunicationBox()
        maskSizer = self.createMaskBox()
        preprocSizer = self.createPreprocessingBox()
        analysisSizer = self.createAnalysisBox()
        outputSizer = self.createOutputBox()
        submitSizer = self.createSubmitBox()

        # add the sizers holding each box to the top level sizer for the panel
        vbox.Add(logoSizer, flag=wx.ALL, border=10, proportion=0)
        vbox.Add(commSizer, flag=wx.EXPAND | wx.ALL, border=10, proportion=0)
        vbox.Add(maskSizer, flag=wx.EXPAND | wx.ALL, border=10, proportion=0)
        vbox.Add(preprocSizer, flag=wx.EXPAND | wx.ALL, border=10, proportion=0)
        vbox.Add(analysisSizer, flag=wx.EXPAND | wx.ALL, border=10, proportion=0)
        vbox.Add(outputSizer, flag=wx.EXPAND | wx.ALL, border=10, proportion=0)
        vbox.Add(submitSizer, flag=wx.EXPAND | wx.ALL, border=10, proportion=0)


        # set the top level sizer to control the master panel
        self.setupPanel.SetSizer(vbox)
        vbox.Fit(self)

        # center the frame on the screen
        self.Centre()

    ### (VIEW) - Panel creation methods ---------------------------------------
    def createLogoBox(self):
        """ draw the top logo panel """
        # top level sizer for this panel
        logoSizer = wx.BoxSizer(wx.HORIZONTAL)  # toplevel sizer for this box

        # add the logo and text images
        logoBMP = wx.Bitmap(join(self.setupGUI_dir, 'images/pynealLogo_200w.bmp'))
        logoImg = wx.StaticBitmap(self.setupPanel, -1, logoBMP)

        textBMP = wx.Bitmap(join(self.setupGUI_dir, 'images/pynealText_200w.bmp'))
        textImg = wx.StaticBitmap(self.setupPanel, -1, textBMP)

        # add images to the toplevel sizer for this panel
        logoSizer.Add(logoImg, flag=wx.LEFT, proportion=0)
        logoSizer.Add(textImg, flag=wx.LEFT, proportion=0)

        return logoSizer

    def createCommunicationBox(self):
        """ draw the Communications box """
        commSizer = wx.BoxSizer(wx.VERTICAL)    # toplevel sizer for this box

        # add  header for this box
        headerImg = self.drawHeader(label='Communication')
        commSizer.Add(headerImg, flag=wx.EXPAND | wx.TOP, proportion=0)

        # main content sizer
        contentSizer = wx.FlexGridSizer(rows=3, cols=2, hgap=5, vgap=5)
        labelW = 180    # width of label col
        entryW = 120    # width of entry col

        ## Host IP row -------------------------------------------------------
        hostText = wx.StaticText(self.setupPanel, -1,
                                 size=(labelW, -1),
                                 style=wx.ALIGN_RIGHT,
                                 label='Pyneal Host IP:')
        self.hostEntry = wx.TextCtrl(self.setupPanel, -1,
                                size=(entryW,-1),
                                style=wx.TE_LEFT,
                                value=self.GUI_settings['pynealHost'])
        contentSizer.Add(hostText, proportion=0, border=5,
                         flag=wx.EXPAND | wx.ALL)
        contentSizer.Add(self.hostEntry, proportion=1,
                         flag=wx.EXPAND | wx.ALL)

        ## Pyneal Scanner Port row --------------------------------------------
        pynealScannerPortText = wx.StaticText(self.setupPanel, -1,
                                              size=(labelW, -1),
                                              style=wx.ALIGN_RIGHT,
                                              label='Pyneal-Scanner Port:')
        self.pynealScannerPortEntry = wx.TextCtrl(self.setupPanel, -1,
                                             size=(entryW, -1),
                                             style=wx.TE_LEFT,
                                             value=str(self.GUI_settings['pynealScannerPort']))
        contentSizer.Add(pynealScannerPortText, proportion=0, border=5,
                         flag=wx.EXPAND | wx.ALL)
        contentSizer.Add(self.pynealScannerPortEntry, proportion=1,
                         flag=wx.EXPAND | wx.ALL)

        ## Results Server Port row --------------------------------------------
        resultsServerPortText = wx.StaticText(self.setupPanel, -1,
                                              size=(labelW, -1),
                                              style=wx.ALIGN_RIGHT,
                                              label='Results Server Port:')
        self.resultsServerPortEntry = wx.TextCtrl(self.setupPanel, -1,
                                             size=(entryW, -1),
                                             style=wx.TE_LEFT,
                                             value=str(self.GUI_settings['resultsServerPort']))
        contentSizer.Add(resultsServerPortText, proportion=0,
                         flag=wx.EXPAND | wx.ALL, border=5)
        contentSizer.Add(self.resultsServerPortEntry, proportion=1,
                         flag=wx.EXPAND | wx.ALL)


        # add content sizer to main box
        commSizer.Add(contentSizer, flag=wx.EXPAND | wx.ALL,
                      proportion=1, border=10)

        return commSizer

    def createMaskBox(self):
        """ draw the mask options box """
        maskSizer = wx.BoxSizer(wx.VERTICAL)

        # add the header for this box
        headerImg = self.drawHeader(label='Mask')
        maskSizer.Add(headerImg, proportion=0, flag=wx.EXPAND | wx.TOP, )

        # main content sizer
        contentSizer = wx.GridBagSizer(vgap=5, hgap=5)

        ## Mask Shape/Name row ------------------------------------------------
        font = self.GetFont()
        font.SetPointSize(12)
        font.SetStyle(wx.FONTSTYLE_ITALIC)
        self.maskShapeText = wx.StaticText(self.setupPanel, -1,
                                      style=wx.ALIGN_RIGHT,
                                      label=self.getMaskShape())
        self.maskShapeText.SetFont(font)
        self.maskNameText = wx.StaticText(self.setupPanel, -1,
                                     style=wx.ALIGN_LEFT,
                                     label=os.path.split(self.GUI_settings['maskFile'])[-1])
        self.maskNameText.SetFont(font)
        contentSizer.Add(self.maskShapeText, pos=(0,0), span=(1,1))
        contentSizer.Add(self.maskNameText, pos=(0,1), span=(1,2),
                         flag=wx.EXPAND | wx.LEFT, border=5)


        ## Mask Path and Dialog Btn row ---------------------------------------
        self.maskPathEntry = wx.TextCtrl(self.setupPanel, -1,
                                    size=(300, -1),
                                    style= wx.TE_LEFT,
                                    value=self.GUI_settings['maskFile'])
        changeBtn = wx.Button(self.setupPanel, -1,
                              label="change")
        changeBtn.Bind(wx.EVT_BUTTON, self.onSelectNewMask)
        contentSizer.Add(self.maskPathEntry, pos=(1,0), span=(1,3), border=5,
                         flag=wx.ALIGN_CENTER_VERTICAL | wx.ALL | wx.EXPAND)
        contentSizer.Add(changeBtn, pos=(1,3), border=5,
                         flag=wx.EXPAND | wx.ALL)
        contentSizer.AddGrowableCol(0,1) # ensure text entry expands with resize

        ## Mask Weighting row -------------------------------------------------
        weightMaskText = wx.StaticText(self.setupPanel, -1,
                                       style=wx.ALIGN_RIGHT,
                                       label='Weighted Mask?')
        self.weightMaskCheckBox = wx.CheckBox(self.setupPanel, -1,
                                         style=wx.CHK_2STATE)
        self.weightMaskCheckBox.SetValue(self.GUI_settings['maskIsWeighted'])
        self.weightMaskCheckBox.Bind(wx.EVT_CHECKBOX, self.onWeightMaskToggled)
        contentSizer.Add(self.weightMaskCheckBox, pos=(2,1), span=(1,1), border=5,
                         flag=wx.ALIGN_RIGHT | wx.ALIGN_CENTER_VERTICAL | wx.TOP)
        contentSizer.Add(weightMaskText, pos=(2,2), span=(1,1), border=5,
                         flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_LEFT | wx.TOP)


        # add content sizer to main box
        maskSizer.Add(contentSizer, flag=wx.EXPAND | wx.ALL,
                      proportion=1, border=10)

        return maskSizer

    def createPreprocessingBox(self):
        """ draw the Preprocessing Box """
        preprocSizer = wx.BoxSizer(wx.VERTICAL)

        # add  header for this box
        headerImg = self.drawHeader(label='Preprocessing')
        preprocSizer.Add(headerImg, flag=wx.EXPAND | wx.TOP, proportion=0)

        # main content sizer
        contentSizer = wx.FlexGridSizer(rows=1, cols=2, hgap=5, vgap=5)
        labelW = 180    # width of label col
        entryW = 120    # width of entry col

        ## numTimepts row ------------------------------------------------------
        numTimeptsText = wx.StaticText(self.setupPanel, -1,
                                 size=(labelW, -1),
                                 style=wx.ALIGN_RIGHT,
                                 label='# of timepts:')
        self.numTimeptsSpin = wx.SpinCtrl(self.setupPanel, -1,
                                size=(entryW,-1),
                                style=wx.SP_ARROW_KEYS,
                                min=0, max=9999)
        self.numTimeptsSpin.SetValue(self.GUI_settings['numTimepts'])
        self.numTimeptsSpin.Bind(wx.EVT_SPINCTRL, self.onNumTimeptsUpdate)
        contentSizer.Add(numTimeptsText, proportion=0, border=5,
                         flag=wx.EXPAND | wx.ALL)
        contentSizer.Add(self.numTimeptsSpin, proportion=1,
                         flag=wx.EXPAND | wx.ALL)

        # add content sizer to main box
        preprocSizer.Add(contentSizer, flag=wx.EXPAND | wx.ALL,
                      proportion=1, border=10)
        return preprocSizer

    def createAnalysisBox(self):
        """ draw the Analysis Box """
        analysisSizer = wx.BoxSizer(wx.VERTICAL)

        # add  header for this box
        headerImg = self.drawHeader(label='Analysis')
        analysisSizer.Add(headerImg, flag=wx.EXPAND | wx.TOP, proportion=0)

        # analysis radio button box
        analysisButtonLabels = ['Average', 'Median', 'Custom']
        self.analysisButtonBox = wx.RadioBox(self.setupPanel, -1,
                                             label='select analysis',
                                             choices=analysisButtonLabels,
                                             majorDimension=1,
                                             style=wx.RA_SPECIFY_ROWS)
        try:
            currentChoiceIdx = analysisButtonLabels.index(self.GUI_settings['analysisChoice'])
        except:
            currentChoiceIdx = analysisButtonLabels.index('Custom')
        self.analysisButtonBox.SetSelection(currentChoiceIdx)
        self.analysisButtonBox.Bind(wx.EVT_RADIOBOX, self.onSelectAnalysis)
        analysisSizer.Add(self.analysisButtonBox, proportion=0, border=5,
                          flag=wx.EXPAND | wx.ALL)

        # analysis info text
        self.analysisText = wx.StaticText(self.setupPanel, -1,
                                          style=wx.ALIGN_CENTRE_HORIZONTAL,
                                          label=self.getAnalysisText())
        self.analysisText.Wrap(200)
        analysisSizer.Add(self.analysisText, proportion=0, border=5,
                          flag=wx.EXPAND | wx.ALL)

        return analysisSizer

    def createOutputBox(self):
        """ draw the output options box """
        outputSizer = wx.BoxSizer(wx.VERTICAL)

        # add the header for this box
        headerImg = self.drawHeader(label='Output')
        outputSizer.Add(headerImg, proportion=0, flag=wx.EXPAND | wx.TOP)

        # main content sizer
        contentSizer = wx.GridBagSizer(vgap=5, hgap=5)

        ## Output Path and Dialog Btn row ---------------------------------------
        self.outputPathEntry = wx.TextCtrl(self.setupPanel, -1,
                                    size=(300, -1),
                                    style=wx.TE_LEFT,
                                    value=self.GUI_settings['outputPath'])
        changeBtn = wx.Button(self.setupPanel, -1,
                              label="change")
        changeBtn.Bind(wx.EVT_BUTTON, self.onSelectNewOutputDir)
        contentSizer.Add(self.outputPathEntry, pos=(0,0), span=(1,3), border=5,
                         flag=wx.ALIGN_CENTER_VERTICAL | wx.ALL | wx.EXPAND)
        contentSizer.Add(changeBtn, pos=(0,3), border=5,
                         flag=wx.EXPAND | wx.ALL)
        contentSizer.AddGrowableCol(0,1) # ensure text entry expands with resize

        ## Launch Dashboard row -------------------------------------------------
        launchDashboardText = wx.StaticText(self.setupPanel, -1,
                                       style=wx.ALIGN_RIGHT,
                                       label='Launch Dashboard?')
        self.launchDashboardCheckBox = wx.CheckBox(self.setupPanel, -1,
                                         style=wx.CHK_2STATE)
        self.launchDashboardCheckBox.SetValue(self.GUI_settings['launchDashboard'])
        self.launchDashboardCheckBox.Bind(wx.EVT_CHECKBOX, self.onLaunchDashboardToggled)
        contentSizer.Add(self.launchDashboardCheckBox, pos=(1,1), span=(1,1), border=5,
                         flag=wx.ALIGN_RIGHT | wx.ALIGN_CENTER_VERTICAL | wx.TOP)
        contentSizer.Add(launchDashboardText, pos=(1,2), span=(1,1), border=5,
                         flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_LEFT | wx.TOP)

        # add content sizer to main box
        outputSizer.Add(contentSizer, flag=wx.EXPAND | wx.ALL,
                      proportion=1, border=10)

        return outputSizer

    def createSubmitBox(self):
        """ create the submit button box """
        submitSizer = wx.BoxSizer(wx.VERTICAL)

        # divider
        bmp = wx.Bitmap(join(self.setupGUI_dir, 'images/headerThin.bmp'))
        headerImg = wx.StaticBitmap(self.setupPanel, -1, bmp)
        submitSizer.Add(headerImg, proportion=0,
                        flag=wx.ALIGN_CENTRE_HORIZONTAL | wx.TOP)

        btnSize = (200, 20)
        submitBtn = wx.Button(self.setupPanel, -1,
                              label='Submit',
                              size=btnSize)
        submitBtn.Bind(wx.EVT_BUTTON, self.onSubmit)

        submitSizer.Add(submitBtn, proportion=0, border=5,
                           flag=wx.ALIGN_CENTRE_HORIZONTAL | wx.ALL)

        return submitSizer

    ### (CONTROL) - Event Handling and User Interaction -----------------------
    def onSelectNewMask(self, e):
        """ open a file dialog for selecting the new mask, and repopulate
        GUI with choice """
        wildcard = '*.gz'
        startDir = os.path.split(self.GUI_settings['maskFile'])[0]
        maskPath = self.openFileDlg(msg="Choose mask (.nii.gz)",
                                    wildcard=wildcard,
                                    startDir=startDir)
        # update mask widgets
        if maskPath is not None:
            if maskPath != self.GUI_settings['maskFile']:
                # set the new mask path
                self.GUI_settings['maskFile'] = maskPath
                self.maskShapeText.SetLabel(self.getMaskShape())
                self.maskNameText.SetLabel(os.path.split(self.GUI_settings['maskFile'])[-1])
                self.maskPathEntry.SetValue(self.GUI_settings['maskFile'])

    def onSelectNewOutputDir(self, e):
        dlg = wx.DirDialog(None, message="Choose output directory...",
                           defaultPath="/Users",
                           style=wx.DD_DEFAULT_STYLE)
        if dlg.ShowModal() == wx.ID_OK:
            path = dlg.GetPath()
            self.GUI_settings['outputPath'] = path
            self.outputPathEntry.SetValue(self.GUI_settings['outputPath'])

    def onWeightMaskToggled(self, e):
        """ update settings & analysis text based on weight mask checkbox """
        self.GUI_settings['maskIsWeighted'] = self.weightMaskCheckBox.GetValue()
        self.analysisText.SetLabel(self.getAnalysisText())

    def onNumTimeptsUpdate(self, e):
        """ update settings based on number of timepts specified """
        self.GUI_settings['numTimepts'] = self.numTimeptsSpin.GetValue()

    def onSelectAnalysis(self, e):
        """ update settings based on analysis selection """
        selectedAnalysis = self.analysisButtonBox.GetStringSelection()
        if selectedAnalysis in ['Average', 'Median']:
            self.GUI_settings['analysisChoice'] = selectedAnalysis
        else:
            customScriptPath = self.openFileDlg(msg="Choose Custom Script (.py)",
                                                wildcard="*.py",
                                                startDir='/Users/jeff')
            self.GUI_settings['analysisChoice'] = customScriptPath

        # set the text for the analysis label
        self.analysisText.SetLabel(self.getAnalysisText())

    def onLaunchDashboardToggled(self, e):
        """ update settings based on launch dashboard checkbox """
        self.GUI_settings['launchDashboard'] = self.launchDashboardCheckBox.GetValue()

    def onSubmit(self, e):
        """ update and confirm all settings and submit """
        # get all settings from GUI
        self.getAllSettings()


        errorCheckPassed = self.check_GUI_settings()
        # write GUI settings to file
        if errorCheckPassed:
            # Convery the GUI_settings from kivy dictproperty to a regular ol'
            # python dict (and do some reformatting along the way)
            allSettings = {}
            for k in self.GUI_settings.keys():
                # convert text inputs to integers
                if k in ['pynealScannerPort', 'resultsServerPort', 'numTimepts']:
                        allSettings[k] = int(self.GUI_settings[k])
                else:
                    allSettings[k] = self.GUI_settings[k]

            # write the settings as the new config yaml file
            with open(self.settingsFile, 'w') as outputFile:
                yaml.dump(allSettings, outputFile, default_flow_style=False)

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
    def drawHeader(self, label="None"):
        """ Draw the header to be placed at the top of the section """
        bmp = wx.Bitmap(join(self.setupGUI_dir, 'images/headerBG.bmp'))
        dc = wx.MemoryDC()
        dc.SelectObject(bmp)
        dc.SetTextForeground("white")
        dc.SetFont(self.headerFont)
        dc.DrawText(label, 15, 8)

        headerImg = wx.StaticBitmap(self.setupPanel, -1, bmp)
        return headerImg

    def getMaskShape(self):
        """ return str with the shape of the mask found at self.GUI_settings['maskFile'] """
        try:
            shape = nib.load(self.GUI_settings['maskFile']).shape
            if len(shape) != 3:
                errMsg = "Mask needs to be 3D (yours has {} dims)".format(len(shape))
                self.showMessageDlg(errMsg, "ERROR", wx.YES_DEFAULT | wx.ICON_EXCLAMATION)
                raise Exception()
            return str(shape)
        except:
            return '(invalid mask)'

    def getAnalysisText(self):
        """ set the text label in the analysis box """
        # determine appropriate label
        if self.GUI_settings['analysisChoice'] == 'Average':
            if self.GUI_settings['maskIsWeighted']:
                label = 'Compute the Weighted Average of voxels within mask'
            else:
                label = 'Compute the Average of voxels within mask'
        elif self.GUI_settings['analysisChoice'] == 'Median':
            if self.GUI_settings['maskIsWeighted']:
                label = 'Compute the Weighted Median of voxels within mask'
            else:
                label = 'Compute the Median of voxels within mask'
        else:
            #label = 'Custom Analysis Script: {}'.format(os.path.split(self.analysisChoice)[-1])
            label = self.GUI_settings['analysisChoice']

        # set the text label
        return label

    def check_GUI_settings(self):
        """ Check the validity of all current GUI settings

        Returns
        -------
        errorCheckPassed : Boolean
            True/False flag indicating whether ALL of the current settings are
            valid or not

        """
        errorMsg = []
        # check if text inputs are valid integers
        for k in ['pynealScannerPort', 'resultsServerPort', 'numTimepts']:
            try:
                tmp = int(self.GUI_settings[k])
            except:
                errorMsg.append('{}: not an integer'.format(k))
                pass

        # check if maskFile is a valid path
        if not os.path.isfile(self.GUI_settings['maskFile']):
            errorMsg.append('{} is not a valid mask file'.format(self.GUI_settings['maskFile']))

        # check if output path is a valid path
        if not os.path.isdir(self.GUI_settings['outputPath']):
            errorMsg.append('{} is not a valid output path'.format(self.GUI_settings['outputPath']))

        # show the error notification, if any
        if len(errorMsg) > 0:
            self.showMessageDlg('\n'.join(errorMsg), 'Settings Error', wx.YES_DEFAULT | wx.ICON_EXCLAMATION)
            errorCheckPassed = False
        else:
            errorCheckPassed = True
        return errorCheckPassed

    def getAllSettings(self):
        """ get all values from the GUI and write into the GUI_settings dict"""
        self.GUI_settings['pynealHost'] = self.hostEntry.GetValue()
        self.GUI_settings['pynealScannerPort'] = self.pynealScannerPortEntry.GetValue()
        self.GUI_settings['resultsServerPort'] = self.resultsServerPortEntry.GetValue()
        self.GUI_settings['maskFile'] = self.maskPathEntry.GetValue()
        self.GUI_settings['maskIsWeighted'] = self.weightMaskCheckBox.GetValue()
        self.GUI_settings['numTimepts'] = self.numTimeptsSpin.GetValue()
        # self.GUI_settings['analysisChoice'] =
        self.GUI_settings['outputPath'] = self.outputPathEntry.GetValue()
        self.GUI_settings['launchDashboard'] = self.launchDashboardCheckBox.GetValue()

        # options that don't appear in GUI, but should be in settings file
        self.GUI_settings['dashboardPort'] = 5557
        self.GUI_settings['dashboardClientPort'] = 5558


class SetupApp(wx.App):
    """ Application class for setup GUI """
    def __init__(self, settingsFile):
        self.settingsFile = settingsFile  # create local reference to settingsFile

        super().__init__()  #initialize the parent wx.App class

    def OnInit(self):
        self.frame = SetupFrame(None,
                                title='Pyneal Setup',
                                settingsFile=self.settingsFile)
        self.frame.Show()
        self.SetTopWindow(self.frame)
        return True


def launchPynealSetupGUI(settingsFile):
    app = SetupApp(settingsFile)
    app.MainLoop()


if __name__ == '__main__':
    # specify settings file to read
    settingsFile = 'setupConfig.yaml'

    # launch setup gui
    launchPynealSetupGUI(settingsFile)
