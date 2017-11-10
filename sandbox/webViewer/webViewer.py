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
import zmq

import logging
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)


context = zmq.Context()
socket = context.socket(zmq.SUB)

app = Flask(__name__)
socketio = SocketIO(app)
thread = None



def background_thread():
    context = zmq.Context()
    socket = context.socket(zmq.SUB)
    socket.setsockopt_string(zmq.SUBSCRIBE, '')
    socket.connect("tcp://127.0.0.1:5556")
    while True:
        msg = socket.recv_string()
        print('received string: {}'.format(msg))

        # send the message to web server
        if msg == 'open':
            print('got open message')
        else:
            socketio.emit('sliceReceived', {'sliceNum': msg})


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
