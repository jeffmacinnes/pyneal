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
        self.setupPanel.SetBackgroundColour("White")

        # create top level sizer that we will add all boxes to
        vbox = wx.BoxSizer(wx.VERTICAL)

        # create the panels
        logoSizer = self.createLogoBox()
        commSizer = self.createCommunicationBox()
        maskSizer = self.createMaskBox()
        preprocSizer = self.createPreprocessingBox()

        # add the sizers holding each box to the top level sizer for the panel
        vbox.Add(logoSizer, flag=wx.EXPAND | wx.ALL, border=10, proportion=0)
        vbox.Add(commSizer, flag=wx.EXPAND | wx.ALL, border=10, proportion=1)
        vbox.Add(maskSizer, flag=wx.EXPAND | wx.ALL, border=10, proportion=1)
        vbox.Add(preprocSizer, flag=wx.EXPAND | wx.ALL, border=10, proportion=1)

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
        logoJPG = wx.Image(join(self.setupGUI_dir, 'images/pynealLogo_200w.jpg'),
                           wx.BITMAP_TYPE_ANY)
        logoImg = wx.StaticBitmap(self.setupPanel, -1, logoJPG.ConvertToBitmap())

        textJPG = wx.Image(join(self.setupGUI_dir, 'images/pynealText_200w.jpg'),
                           wx.BITMAP_TYPE_ANY)
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

        ## Host IP row -------------------------------------------------------
        hostText = wx.StaticText(self.setupPanel, -1, size=(labelW, -1),
                                 style=wx.ALIGN_RIGHT, label='Pyneal Host IP:')
        hostEntry = wx.TextCtrl(self.setupPanel, -1, size=(entryW,-1),
                                style=wx.TE_LEFT, value='127.0.0.1')
        contentSizer.Add(hostText, proportion=0, flag=wx.EXPAND | wx.ALL,
                         border=5)
        contentSizer.Add(hostEntry, proportion=1, flag=wx.EXPAND | wx.ALL)

        ## Pyneal Scanner Port row --------------------------------------------
        pynealScannerPortText = wx.StaticText(self.setupPanel, -1,
                                              size=(labelW, -1),
                                              style=wx.ALIGN_RIGHT,
                                              label='Pyneal-Scanner Port:')
        pynealScannerPortEntry = wx.TextCtrl(self.setupPanel, -1,
                                             size=(entryW, -1),
                                             style=wx.TE_LEFT,
                                             value='5555')
        contentSizer.Add(pynealScannerPortText, proportion=0,
                         flag=wx.EXPAND | wx.ALL, border=5)
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
        maskSizer.Add(headerImg, flag=wx.EXPAND | wx.TOP, proportion=0)

        # main content sizer
        contentSizer = wx.GridBagSizer(vgap=5, hgap=5)

        ## Mask Shape/Name row ------------------------------------------------
        font = self.GetFont()
        font.SetPointSize(12)
        font.SetStyle(wx.FONTSTYLE_ITALIC)
        maskShapeText = wx.StaticText(self.setupPanel, -1, style=wx.ALIGN_RIGHT,
                                      label=self.getMaskShape())
        maskShapeText.SetFont(font)
        maskNameText = wx.StaticText(self.setupPanel, -1, style=wx.ALIGN_LEFT,
                                     label=os.path.split(self.maskPath)[-1])
        maskNameText.SetFont(font)
        contentSizer.Add(maskShapeText, pos=(0,0), span=(1,1))
        contentSizer.Add(maskNameText, pos=(0,1), span=(1,2),
                         flag=wx.EXPAND | wx.LEFT, border=5)


        ## Mask Path and Dialog Btn row ---------------------------------------
        maskPathEntry = wx.TextCtrl(self.setupPanel, -1, size=(300, -1),
                                     style= wx.TE_LEFT, value=self.maskPath)
        changeBtn = wx.Button(self.setupPanel, -1, label="change")
        changeBtn.SetForegroundColour("red")
#                            size=(bmp.GetWidth()+25, bmp.GetHeight()+10))
        contentSizer.Add(maskPathEntry, pos=(1,0), span=(1,3),
                         flag=wx.ALIGN_CENTER_VERTICAL | wx.ALL | wx.EXPAND, border=5)
        contentSizer.Add(changeBtn, pos=(1,3), flag=wx.EXPAND | wx.ALL, border=5)
        contentSizer.AddGrowableCol(0,1)


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

    def truncatePath(self, string, desiredWidth):
        font = self.GetFont()
        dc = wx.ScreenDC()
        dc.SetFont(font)
        w,h = dc.GetTextExtent(string)
        while w > desiredWidth-10:
            string = string[1:]
            w,h = dc.GetTextExtent(string)
        string = '...' + string[3:]
        print(string)
        return string

    def getMaskShape(self):
        """ return the shape of the mask found at self.maskPath """
        try:
            shape = nib.load(self.maskPath).shape
            return str(shape)
        except:
            return '(none)'


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
