"""
App to host the backend of the Pyneal Dashboard for monitoring a real-time
scan.

"""

import os
import zmq
import time














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



if __name__ == '__main__':

    context = zmq.Context.instance()
    dashboardSocket = context.socket(zmq.REP)
    dashboardPort = dashboardSocket.bind_to_random_port('tcp://127.0.0.1',
                                                    min_port=8000, max_port=8100)
    print(dashboardPort)
