import wuy

class helloWorld(wuy.Window):
    size=(400, 800)

    def beep(self):
        print('\a BEEP !!!')

    def myadd(self, a, b):
        return a+b

helloWorld()
