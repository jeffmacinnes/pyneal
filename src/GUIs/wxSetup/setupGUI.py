import os
from os.path import join

import wx

pynealColor = '#B04555'


class SetupFrame(wx.Frame):
    def __init__(self, parent, title="Pyneal Setup"):
        super(SetupFrame, self).__init__(parent, title=title)  #initialize the parent class
        self.setupGUI_dir = os.path.dirname(os.path.abspath(__file__))

        # initialize all gui panels and settings
        self.InitUI()

    def InitUI(self):
        """ Initialize all GUI windows and widgets """

        # set defaults
        font = self.GetFont()
        font.SetFaceName('Helvetica')
        font.SetPointSize(15)
        self.SetFont(font)

        self.setupPanel = wx.Panel(self, -1)
        self.setupPanel.SetBackgroundColour("White")
        self.headerFont = wx.Font(wx.FontInfo(20).FaceName('Helvetica').Bold().AntiAliased(True))

        vbox = wx.BoxSizer(wx.VERTICAL)

        self.Centre()

        # create the panels
        logoSizer = self.createLogoBox()
        commSizer = self.createCommunicationBox()
        preprocSizer = self.createPreprocessingBox()

        vbox.Add(logoSizer, flag=wx.EXPAND | wx.ALL, border=10, proportion=0)
        vbox.Add(commSizer, flag=wx.EXPAND | wx.ALL, border=10, proportion=1)
        vbox.Add(preprocSizer, flag=wx.EXPAND | wx.ALL, border=10, proportion=1)

        # self.createMaskBox()
        # self.createPreprocessingBox()
        # self.createAnalysisBox()
        # self.createOutputBox()
        # self.createSubmitBox()
        self.setupPanel.SetSizer(vbox)
        vbox.Fit(self)

    ### (VIEW) - Panel creation methods ---------------------------------------
    def createLogoBox(self):
        """ draw the top logo panel """
        # top level sizer for this panel
        logoSizer = wx.BoxSizer(wx.HORIZONTAL)  # toplevel sizer for this box

        # add the logo and text images
        logoJPG = wx.Image(join(self.setupGUI_dir, 'images/pynealLogo_200w.jpg'), wx.BITMAP_TYPE_ANY)
        logoImg = wx.StaticBitmap(self.setupPanel, -1, logoJPG.ConvertToBitmap())

        textJPG = wx.Image(join(self.setupGUI_dir, 'images/pynealText_200w.jpg'), wx.BITMAP_TYPE_ANY)
        textImg = wx.StaticBitmap(self.setupPanel, -1, textJPG.ConvertToBitmap())

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

        # host IP row
        hostText = wx.StaticText(self.setupPanel, -1, size=(labelW, -1), style=wx.ALIGN_RIGHT, label='Pyneal Host IP:')
        hostEntry = wx.TextCtrl(self.setupPanel, -1, size=(entryW,-1), style=wx.TE_LEFT, value='127.0.0.1')
        contentSizer.Add(hostText, proportion=0, flag=wx.EXPAND | wx.ALL, border=5)
        contentSizer.Add(hostEntry, proportion=1, flag=wx.EXPAND | wx.ALL)

        # Pyneal-Scanner Port row
        pynealScannerPortText = wx.StaticText(self.setupPanel, -1, size=(labelW, -1), style=wx.ALIGN_RIGHT, label='Pyneal-Scanner Port:')
        pynealScannerPortEntry = wx.TextCtrl(self.setupPanel, -1, size=(entryW, -1), style=wx.TE_LEFT, value='5555')
        contentSizer.Add(pynealScannerPortText, proportion=0, flag=wx.EXPAND | wx.ALL, border=5)
        contentSizer.Add(pynealScannerPortEntry, proportion=1, flag=wx.EXPAND | wx.ALL)

        # Results Server Port row
        resultsServerPortText = wx.StaticText(self.setupPanel, -1, size=(labelW, -1), style=wx.ALIGN_RIGHT, label='Results Server Port:')
        resultsServerPortEntry = wx.TextCtrl(self.setupPanel, -1, size=(entryW, -1), style=wx.TE_LEFT, value='5556')
        contentSizer.Add(resultsServerPortText, proportion=0, flag=wx.EXPAND | wx.ALL, border=5)
        contentSizer.Add(resultsServerPortEntry, proportion=1, flag=wx.EXPAND | wx.ALL)


        # add content sizer to main box
        commSizer.Add(contentSizer, flag=wx.EXPAND | wx.ALL, proportion=1, border=10)

        return commSizer

    def createPreprocessingBox(self):
        """ draw the Preprocessing Box """
        preprocSizer = wx.BoxSizer(wx.VERTICAL)    # toplevel sizer for this box

        # add  header for this box
        headerImg = self.drawHeader(label='Preprocessing')
        preprocSizer.Add(headerImg, flag=wx.EXPAND | wx.TOP, proportion=0)

        return preprocSizer


    ### (CONTROL) - Event Handling and User Interaction -----------------------
    # def OnPaint(self, e):
    #     for hp in self.headerPanels:
    #         self.drawHeader(hp)

    def drawHeader(self, label="None"):
        headerJPG = wx.Image(join(self.setupGUI_dir, 'images/headerBG.jpg'), wx.BITMAP_TYPE_ANY)

        bmp = wx.Image(join(self.setupGUI_dir, 'images/headerBG.jpg'), wx.BITMAP_TYPE_ANY).ConvertToBitmap()
        dc = wx.MemoryDC()
        dc.SelectObject(bmp)
        dc.SetTextForeground("white")
        dc.SetFont(self.headerFont)
        dc.DrawText(label, 15, 8)

        headerImg = wx.StaticBitmap(self.setupPanel, -1, bmp)
        return headerImg



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
