"""
App to host the backend of the Pyneal Dashboard for monitoring a real-time
scan.

"""

import sys
import os
import time
from threading import Thread

import zmq

from flask import Flask, render_template
from flask_socketio import SocketIO, send, emit
import eventlet
eventlet.monkey_patch()


# initialize flask app
app = Flask(__name__)
socketio = SocketIO(app)


# vars to store incoming data
allData = {'volNum': [],
            'motion': []}


class DashboardIPCServer(Thread):
    """
    Class to run in the background, listen for incoming IPC messages, parse,
    and pass along to the client web browser via socketio
    """
    def __init__(self, socket):
        # start the thread upon creation
        Thread.__init__(self)

        # get local reference to socket
        self.ipc_socket = socket

        # dashboard data
        self.configSettings = None

        self.alive = True

    def run(self):
        while self.alive:
            try:
                # listen for incoming JSON messages from pyneal
                msg = self.ipc_socket.recv_json(flags=zmq.NOBLOCK)
                self.ipc_socket.send_string('got message')

                # process this particular message
                self.processMsg(msg)

            except zmq.Again as e:
                pass
            time.sleep(.05)

    def processMsg(self, msg):
        """
        process the incoming message to figure out what kind of data it
        contains. Each message is assumed to be a dictionary with 2 keys:
          'topic': indicates what kind of data this message contains
          'content': the actual content of the message; can be anything
                        from a simple integer to a dictionary of multiple vals.
                        A given topic should always have similarly formatted
                        content to ensure it gets handled appropriately on this
                        end
        E.g.
              msg = {'topic':'volNum',
                      'content':25}

        messages are processed differently according to their topic, so make
        sure the content is appropriate to the topics
        """

        if msg['topic'] == 'configSettings':
            print(msg)
            #self.configSettings = msg['content']

            # send to client
            socketio.emit('configSettings', msg['content'])
            pass

        elif msg['topic'] == 'volNum':
            print(msg)
            socketio.emit('volNum', msg['content'])
            pass


# use decorators to link function to a URL
@app.route('/')
def pynealWatcher():
    return render_template('pynealDashboard.html')

# method for when web browser client connects
@socketio.on('connect')
def handle_client_connect_event():
    print('browser connected huzzah')
    global thread


def launchDashboard(ipc_socket):
    """
    start the app. Use the supplied socket to listen in for incoming messages
    that will be parsed and sent to the client's web browser
    """

    # start the background thread to listen for incoming interprocess communication
    # messages from various Pyneal modules
    ipc_thread = IPC_Server(ipc_socket)
    ipc_thread.daemon = True
    ipc_thread.start()

    # launch the webserver that will host the dashboard. A web browser can
    # access the dashboard by going to http://127.0.0.1:<clientPort>
    clientPort = 9999
    socketio.run(app, port=clientPort)


# Calling this script directly will start the webserver and create a zmq socket
# that will listen for incoming inter-process communication (IPC) messages on the
# port specified by 'dashboardPort'. It will host the dashboard website on the port
# specified by 'dashboardClientPort' (website at 127.0.0.1:<dashboardClientPort>)
if __name__ == '__main__':

    ### set up the socket that the dashboard will use to listen for incoming IPC
    dashboardPort = int(sys.argv[1])
    context = zmq.Context.instance()
    dashboardSocket = context.socket(zmq.REP)
    dashboardSocket.bind('tcp://127.0.0.1:{}'.format(dashboardPort))

    ### start the server listening for incoming ipc messages
    dashboardServer = DashboardIPCServer(dashboardSocket)
    dashboardServer.daemon = True
    dashboardServer.start()

    ### launch the webserver
    dashboardClientPort = int(sys.argv[2])
    print(dashboardClientPort)
    socketio.run(app, port=dashboardClientPort)
