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

        self.setupPanel = wx.Panel(self, -1)
        self.setupPanel.SetBackgroundColour("White")
        self.headerFont = wx.Font(wx.FontInfo(22).FaceName('Helvetica').Bold().AntiAliased(True))

        vbox = wx.BoxSizer(wx.VERTICAL)

        self.Centre()

        # create the panels
        logoSizer = self.createLogoBox()
        commSizer = self.createCommunicationBox()
        preprocSizer = self.createPreprocessingBox()

        vbox.Add(logoSizer, flag=wx.EXPAND | wx.ALL, border=10, proportion=1)
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
        #commSizer.Add(label, flag=wx.EXPAND | wx.TOP, border=5, proportion=0)

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
        dc.DrawText(label, 15, 15)

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
