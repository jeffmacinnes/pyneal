import os

from kivy.app import App
from kivy.uix.gridlayout import GridLayout
from kivy.uix.button import Button
from kivy.lang import Builder
from kivy.properties import ObjectProperty
from kivy.core.window import Window

Window.clearcolor = (1,1,1,1)

# load all of the kv files
kv_path = './kv/'
for kv in os.listdir(kv_path):
    Builder.load_file(kv_path+kv)

class AddButton(Button):
    pass

class SubtractButton(Button):
    pass

class Container(GridLayout):
    display = ObjectProperty()

    def add_one(self):
        value = int(self.display.text)
        self.display.text = str(value+1)

    def subtract_one(self):
        value = int(self.display.text)
        self.display.text = str(value-1)


class MainApp(App):
    def build(self):
        self.title = 'Pyneal Setup'
        return Container()

if __name__ == '__main__':
    app = MainApp()
    app.run()
