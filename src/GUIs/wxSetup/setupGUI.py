import wx
print(wx.__version__)
pynealColor = '#C74053'


class SetupFrame(wx.Frame):
    def __init__(self, parent, title="Pyneal Setup"):
        super(SetupFrame, self).__init__(parent, title=title)  #initialize the parent class
        self.InitUI()

    def InitUI(self):
        self.Centre()

        # create the panels
        self.createLogoPanel()
        self.createCommunicationPanel()
        # self.createMaskPanel()
        # self.createPreprocessingPanel()
        # self.createAnalysisPanel()
        # self.createOutputPanel()
        # self.createSubmitPanel()

    ### (VIEW) - Panel creation methods ---------------------------------------
    def createLogoPanel(self):
        pass

    def createCommunicationPanel(self):
        pass

    ### (CONTROL) - Event Handling and User Interaction -----------------------

    def OnMove(self, e):
        x, y = e.GetPosition()
        self.st1.SetLabel(str(x))
        self.st2.SetLabel(str(y))


class SetupApp(wx.App):
    """ Application class for setup GUI """

    def OnInit(self):
        self.frame = SetupFrame(None) #, title='fuck you')
        self.frame.Show()
        self.SetTopWindow(self.frame)
        return True


def launchPynealSetupGUI():
    app = SetupApp()
    app.MainLoop()


if __name__ == '__main__':

    # create settings dict to pass into

    launchPynealSetupGUI()
