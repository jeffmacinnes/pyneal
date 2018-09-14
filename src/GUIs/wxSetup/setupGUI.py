import os
from os.path import join

import wx
import nibabel as nib

pynealColor = '#B04555'


class SetupFrame(wx.Frame):
    def __init__(self, parent, title="Pyneal Setup"):
        super(SetupFrame, self).__init__(parent, title=title)  #initialize the parent class
        self.setupGUI_dir = os.path.dirname(os.path.abspath(__file__))

        # initialize all gui panels and settings
        self.InitSettings()
        self.InitUI()

    def InitSettings(self):
        """ Initialize values for all settings """
        self.maskPath = '/Users/jeff/gDrive/jeffCloud/real-time/pyneal/tests/testData/testSeries_mask.nii.gz'
        self.weightMaskChoice = True
        self.numTimepts = 60
        self.analysisChoice = '/path/to/customScript.py'

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

        # add the sizers holding each box to the top level sizer for the panel
        vbox.Add(logoSizer, flag=wx.ALL, border=10, proportion=0)
        vbox.Add(commSizer, flag=wx.EXPAND | wx.ALL, border=10, proportion=0)
        vbox.Add(maskSizer, flag=wx.EXPAND | wx.ALL, border=10, proportion=0)
        vbox.Add(preprocSizer, flag=wx.EXPAND | wx.ALL, border=10, proportion=0)
        vbox.Add(analysisSizer, flag=wx.EXPAND | wx.ALL, border=10, proportion=0)
        vbox.Add(outputSizer, flag=wx.EXPAND | wx.ALL, border=10, proportion=0)

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
        hostEntry = wx.TextCtrl(self.setupPanel, -1,
                                size=(entryW,-1),
                                style=wx.TE_LEFT,
                                value='127.0.0.1')
        contentSizer.Add(hostText, proportion=0, border=5,
                         flag=wx.EXPAND | wx.ALL)
        contentSizer.Add(hostEntry, proportion=1,
                         flag=wx.EXPAND | wx.ALL)

        ## Pyneal Scanner Port row --------------------------------------------
        pynealScannerPortText = wx.StaticText(self.setupPanel, -1,
                                              size=(labelW, -1),
                                              style=wx.ALIGN_RIGHT,
                                              label='Pyneal-Scanner Port:')
        pynealScannerPortEntry = wx.TextCtrl(self.setupPanel, -1,
                                             size=(entryW, -1),
                                             style=wx.TE_LEFT,
                                             value='5555')
        contentSizer.Add(pynealScannerPortText, proportion=0, border=5,
                         flag=wx.EXPAND | wx.ALL)
        contentSizer.Add(pynealScannerPortEntry, proportion=1,
                         flag=wx.EXPAND | wx.ALL)

        ## Results Server Port row --------------------------------------------
        resultsServerPortText = wx.StaticText(self.setupPanel, -1,
                                              size=(labelW, -1),
                                              style=wx.ALIGN_RIGHT,
                                              label='Results Server Port:')
        resultsServerPortEntry = wx.TextCtrl(self.setupPanel, -1,
                                             size=(entryW, -1),
                                             style=wx.TE_LEFT,
                                             value='5556')
        contentSizer.Add(resultsServerPortText, proportion=0,
                         flag=wx.EXPAND | wx.ALL, border=5)
        contentSizer.Add(resultsServerPortEntry, proportion=1,
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
                                     label=os.path.split(self.maskPath)[-1])
        self.maskNameText.SetFont(font)
        contentSizer.Add(self.maskShapeText, pos=(0,0), span=(1,1))
        contentSizer.Add(self.maskNameText, pos=(0,1), span=(1,2),
                         flag=wx.EXPAND | wx.LEFT, border=5)


        ## Mask Path and Dialog Btn row ---------------------------------------
        self.maskPathEntry = wx.TextCtrl(self.setupPanel, -1,
                                    size=(300, -1),
                                    style= wx.TE_LEFT,
                                    value=self.maskPath)
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
        self.weightMaskCheckBox.SetValue(self.weightMaskChoice)
        self.weightMaskCheckBox.Bind(wx.EVT_CHECKBOX, self.onWeightMaskToggled)
        contentSizer.Add(self.weightMaskCheckBox, pos=(2,0), span=(1,1), border=5,
                         flag=wx.ALIGN_RIGHT | wx.ALIGN_CENTER_VERTICAL | wx.TOP)
        contentSizer.Add(weightMaskText, pos=(2,1), span=(1,1), border=5,
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
        self.numTimeptsSpin.SetValue(self.numTimepts)
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
            currentChoiceIdx = analysisButtonLabels.index(self.analysisChoice)
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
        """ draw the Output Box """
        outputSizer = wx.BoxSizer(wx.VERTICAL)

        # add  header for this box
        headerImg = self.drawHeader(label='Output')
        outputSizer.Add(headerImg, flag=wx.EXPAND | wx.TOP, proportion=0)

        return outputSizer


    ### (CONTROL) - Event Handling and User Interaction -----------------------
    def onSelectNewMask(self, e):
        """ open a file dialog for selecting the new mask, and repopulate
        GUI with choice """
        wildcard = '*.gz'
        startDir = os.path.split(self.maskPath)[0]
        maskPath = self.openFileDlg(msg="Choose mask (.nii.gz)",
                                    wildcard=wildcard,
                                    startDir=startDir)
        # update mask widgets
        if maskPath is not None:
            if maskPath != self.maskPath:
                # set the new mask path
                self.maskPath = maskPath
                self.maskShapeText.SetLabel(self.getMaskShape())
                self.maskNameText.SetLabel(os.path.split(self.maskPath)[-1])
                self.maskPathEntry.SetValue(self.maskPath)

    def onWeightMaskToggled(self, e):
        """ update settings & analysis text based on weight mask checkbox """
        self.weightMaskChoice = self.weightMaskCheckBox.GetValue()
        self.analysisText.SetLabel(self.getAnalysisText())


    def onNumTimeptsUpdate(self, e):
        """ update settings based on number of timepts specified """
        self.numTimepts = self.numTimeptsSpin.GetValue()

    def onSelectAnalysis(self, e):
        """ update settings based on analysis selection """
        selectedAnalysis = self.analysisButtonBox.GetStringSelection()
        if selectedAnalysis in ['Average', 'Median']:
            self.analysisChoice = selectedAnalysis
        else:
            customScriptPath = self.openFileDlg(msg="Choose Custom Script (.py)",
                                                wildcard="*.py",
                                                startDir='/Users/jeff')
            self.analysisChoice = customScriptPath

        self.analysisText.SetLabel(self.getAnalysisText())


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
        """ return str with the shape of the mask found at self.maskPath """
        try:
            shape = nib.load(self.maskPath).shape
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
        if self.analysisChoice == 'Average':
            if self.weightMaskChoice:
                label = 'Compute the Weighted Average of voxels within mask'
            else:
                label = 'Compute the Average of voxels within mask'
        elif self.analysisChoice == 'Median':
            if self.weightMaskChoice:
                label = 'Compute the Weighted Median of voxels within mask'
            else:
                label = 'Compute the Median of voxels within mask'
        else:
            label = 'Custom Analysis Script: {}'.format(os.path.split(self.analysisChoice)[-1])

        # set the text label
        return label


class SetupApp(wx.App):
    """ Application class for setup GUI """

    def OnInit(self):
        self.frame = SetupFrame(None, title='Pyneal Setup')
        self.frame.Show()
        self.SetTopWindow(self.frame)
        return True


def launchPynealSetupGUI():
    app = SetupApp()
    app.MainLoop()


if __name__ == '__main__':

    # create settings dict to pass into

    launchPynealSetupGUI()
