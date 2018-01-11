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
import sys

app = Flask(__name__)
socketio = SocketIO(app)
app.config['SECRET_KEY'] = 'secret!'
thread = Thread()

allData = {'sliceNum': [],
            'motion': []}

class BackgroundTask(Thread):
    def __init__(self, webServerPort):
        # start the thread upon creation
        Thread.__init__(self)

        context = zmq.Context()
        self.pynealSocket = context.socket(zmq.SUB)
        self.pynealSocket.setsockopt_string(zmq.SUBSCRIBE, '')
        self.pynealSocket.connect("tcp://127.0.0.1:{}".format(webServerPort))

    def run(self):
        self.sendDataToClient()

    def sendDataToClient(self):
        while True:
            try:
                msg = self.pynealSocket.recv_json(flags=zmq.NOBLOCK)
                print('Received from pyneal: {}'.format(msg))

                # parse message
                if msg['msgTopic'] == 'sliceNum':
                    allData['sliceNum'].append(msg['data'])
                    print('sliceNum: {}'.format(msg['data']))
                elif msg['msgTopic'] == 'motion':
                    allData['motion'].append(msg['data'])
                    print('motion: {}'.format(msg['data']))

                print('sending to browser: ', allData)
                socketio.emit('newMessage', allData)
            except zmq.Again as e:
                # no messages yet
                pass
            time.sleep(.1)


# use decorators to link function to a URL
@app.route('/')
def pynealWatcher():
    return render_template('pynealWatcher.html')

# method for when web browser client connects
@socketio.on('connect')
def handle_client_connect_event():
    print('browser connected')
    socketio.emit('newMessage', allData)
    global thread


if __name__ == "__main__":
    webServerPort = sys.argv[1]

    # open browser
    #os.system('open http://127.0.0.1:{}'.format(port))

    # start the background task
    task = BackgroundTask(webServerPort)
    task.daemon = True
    task.start()

    # launch the webserver
    server2browser_port = 5000
    socketio.run(app, port=server2browser_port)
