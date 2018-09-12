import os

import eel


web_app_options = {
    'mode': 'chrome-app',
    'host': '127.0.0.1',
    'port': 0,
    'chromeFlags': [' --window-size=500,500']
}

web_location = 'web'
web_path = os.path.dirname(os.path.realpath(__file__)) + '/' + web_location

eel.init(web_path)
eel.start('main.html', size=(400, 800), options=web_app_options)
