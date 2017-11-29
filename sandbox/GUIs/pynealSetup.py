from kivy.app import App
from kivy.uix.widget import Widget
from kivy.uix.gridlayout import GridLayout



class SetupGUI(Widget):
    pass


class SetupApp(App):
    """
    Root App class. Calling run method on this class launches
    the GUI
    """

    def build(self):
        self.title = 'Pyneal Setup'
        return SetupGUI()




if __name__ == '__main__':
    settings = {}
    settings['scannerPort'] = 5555
    settings['outputPort'] = 5556

    # instantiate the app
    app = SetupApp()
    app.run()
