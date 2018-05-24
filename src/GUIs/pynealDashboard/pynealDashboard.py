"""
Flask-based App to host the backend of the Pyneal Dashboard for
monitoring a real-time scan.

In addition to providing a webserver for the dashboard, this tool will
listen for interprocess communication messages sent from the main
Pyneal processes, which it will parse and send along to any client
browsers that are viewing the dashboard. The client-side javascript will
interpret the messages and update the dashboard accordingly
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
existingData = {'mask': '',
            'analysisChoice': '',
            'volDims': '',
            'numTimepts': None,
            'outputPath': '',
            'currentVolIdx': 0,
            'motion': [],
            'timePerVol': []
            }


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
        """
        While the IPC server is running, it will listen for new incoming JSON
        messages, and process according to the 'topic' field of the message
        """
        while self.alive:
            try:
                # listen for incoming JSON messages from pyneal
                msg = self.ipc_socket.recv_json(flags=zmq.NOBLOCK)
                self.ipc_socket.send_string('success')

                # process this particular message
                self.processMsg(msg)

            except zmq.Again as e:
                pass
            time.sleep(.1)


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
              msg = {'topic':'volIdx',
                      'content':25}

        messages are processed differently according to their topic.

        In addition, each time a new message appears, it's contents get added
        to the existingData dictionary. This dictionary gets sent to the client
        upon first connecting to the page. This way, if the client breaks the
        connection partway through the scan, they can still receive all of
        the existing data
        """
        if msg['topic'] == 'configSettings':
            # update existing data
            existingData['mask'] = msg['content']['mask']
            existingData['analysisChoice'] = msg['content']['analysisChoice']
            existingData['volDims'] = msg['content']['volDims']
            existingData['numTimepts'] = msg['content']['numTimepts']
            existingData['outputPath'] = msg['content']['outputPath']

            # send to client
            socketio.emit('configSettings', msg['content'])

        elif msg['topic'] == 'volIdx':
            # update existing data
            existingData['currentVolIdx'] = msg['content']

            # send to client
            socketio.emit('volIdx', msg['content'])

        elif msg['topic'] == 'motion':
            # update existing data
            existingData['motion'].append(msg['content'])

            # send to client
            socketio.emit('motion', msg['content'])

        elif msg['topic'] == 'timePerVol':
            # update existing data
            existingData['timePerVol'].append(msg['content'])

            # send to client
            socketio.emit('timePerVol', msg['content'])

        elif msg['topic'] == 'pynealScannerLog':
            # send to client
            socketio.emit('pynealScannerLog', msg['content'])

        elif msg['topic'] == 'resultsServerLog':
            # send to client
            socketio.emit('resultsServerLog', msg['content'])


# Root dashboard page
@app.route('/')
def pynealWatcher():
    return render_template('pynealDashboard.html')


# Method for when web browser client connects
@socketio.on('connect')
def handle_client_connect_event():
    # when the client connects, send all existing data
    print('dashboard client connected, sending any existing data...')
    socketio.emit('existingData', existingData)
    global thread


# Method to launch dashboard
def launchDashboard(dashboardPort=9998, clientPort=9999):
    """
    start the app. Use the supplied socket to listen in for incoming messages
    that will be parsed and sent to the client's web browser
    """

    ### set up the socket that the dashboard will use to listen for incoming IPC
    dashboardPort = int(sys.argv[1])
    context = zmq.Context.instance()
    dashboardSocket = context.socket(zmq.REP)
    dashboardSocket.bind('tcp://127.0.0.1:{}'.format(dashboardPort))

    ### start listening for incoming ipc messages
    dashboardServer = DashboardIPCServer(dashboardSocket)
    dashboardServer.daemon = True
    dashboardServer.start()

    # launch the server
    socketio.run(app, port=clientPort)



# Calling this script directly will start the webserver and create a zmq socket
# that will listen for incoming inter-process communication (IPC) messages on the
# port specified by 'dashboardPort'. It will host the dashboard website on the port
# specified by 'dashboardClientPort' (website at 127.0.0.1:<dashboardClientPort>)
if __name__ == '__main__':

    if len(sys.argv) < 2:
        print('Please specify a dashboard port, and a client port')
        print('e.g. python pynealDashboard.py 5555 5556')

    # launch the dashboard using the supplied ports
    launchDashboard(dashboardPort=int(sys.argv[1]), clientPort=int(sys.argv[2]))
