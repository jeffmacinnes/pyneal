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
        newText = ''.join(random.choice(string.ascii_lowercase) for _ in range(10))
        print('sent {}'.format(newText))
        socketio.emit('message', {'newText': newText})
        time.sleep(2)

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
