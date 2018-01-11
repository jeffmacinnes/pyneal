import zmq
import sys
import time
import os
import subprocess
import sys
import numpy as np

webServerPort = 8888

# set up publish port
context = zmq.Context()
socket = context.socket(zmq.PUB)
socket.bind('tcp://127.0.0.1:{}'.format(webServerPort))

### Launch webserver
pythonPath = sys.executable
webserver = subprocess.Popen([pythonPath, 'app.py', str(webServerPort)])
print('launch')
time.sleep(5)

counter = 0
while True:
    # send sliceNumber message
    message = {'msgTopic':'sliceNum', 'data':str(np.random.randint(100))}
    print('sent to webserver {}'.format(message))
    socket.send_json(message)

    # send motion message
    message = {'msgTopic':'motion', 'data':str(np.random.randint(100))}
    print('sent to webserver {}'.format(message))
    socket.send_json(message)

    # increment sliceNumber
    time.sleep(1)
    counter += 1

    if counter >= 10:
        break


webserver.kill()
print('killed')
