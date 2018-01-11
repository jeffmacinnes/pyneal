import os

from flask import Flask
from flask import render_template
from flask_socketio import SocketIO
from flask_socketio import send, emit
import eventlet
eventlet.monkey_patch()

from threading import Thread

import zmq
import time

app = Flask(__name__)
socketio = SocketIO(app)
app.config['SECRET_KEY'] = 'secret!'
thread = Thread()


class BackgroundTask(Thread):
    def __init__(self):
        # start the thread upon creation
        Thread.__init__(self)

        context = zmq.Context()
        self.pynealSocket = context.socket(zmq.SUB)
        self.pynealSocket.setsockopt_string(zmq.SUBSCRIBE, '')
        self.pynealSocket.connect("tcp://127.0.0.1:8888")

    def run(self):
        self.sendDataToClient()

    def sendDataToClient(self):
        while True:
            msg = self.pynealSocket.recv_json()
            print('Received from pyneal: {}'.format(msg))

            print('sending: ', msg)
            socketio.emit('newMessage', msg)
            time.sleep(.1)


# use decorators to link function to a URL
@app.route('/')
def pynealWatcher():
    return render_template('pynealWatcher.html')

# method for when web browser client connects
@socketio.on('connect')
def handle_client_connect_event():
    print('browser connected')
    global thread
    task = BackgroundTask()
    task.start()


if __name__ == "__main__":
    port = 5000

    # open browser
    #os.system('open http://localhost:{}'.format(port))

    socketio.run(app)
