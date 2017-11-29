from kivy.app import App
from kivy.uix.widget import Widget
from kivy.uix.boxlayout import BoxLayout

# Set Window Size
from kivy.config import Config
Config.set('graphics', 'width', '400')
Config.set('graphics', 'height', '700')

class MainContainer(BoxLayout):
    """
    Custom widget that is the root level container for all
    other widgets
    """
    pass


class SetupApp(App):
    """
    Root App class. Calling run method on this class launches
    the GUI
    """
    title = 'Pyneal Setup'
    pass

if __name__ == '__main__':
    # run the app
    SetupApp().run()
