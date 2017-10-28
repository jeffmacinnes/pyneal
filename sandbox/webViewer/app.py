"""
Testing out building a dynamic web-based front end for running pyneal
"""

from flask import Flask
from flask import render_template
from flask_socketio import SocketIO
from flask_socketio import send, emit
import time
import random
import string

app = Flask(__name__)
socketio = SocketIO(app)
thread = None



def background_thread():
    while True:
        newH1= ''.join(random.choice(string.ascii_lowercase) for _ in range(10))
        print('sent {}'.format(newH1))
        socketio.emit('headerText', {'value': newH1})

        newH2 = str(random.choice([1,2,3,4,5,6,7]))
        print('sent {}'.format(newH2))
        socketio.emit('header2Text', {'value': newH2})
        time.sleep(1)


@socketio.on('client_connected')
def handle_client_connect_event(json):
    print('received json: {0}'.format(str(json)))
    global thread
    if thread is None:
        thread = socketio.start_background_task(target=background_thread)



@app.route('/')
def index():
    return render_template('index.html')


if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0')
