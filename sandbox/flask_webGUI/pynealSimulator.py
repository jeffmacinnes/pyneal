import zmq
import sys
import time

port = 8888

# set up publish port
context = zmq.Context()
socket = context.socket(zmq.PUB)
socket.bind('tcp://127.0.0.1:{}'.format(port))

sliceNum = 0
while True:
    #topic = 'sliceNum'
    message = {'sliceNumber': str(sliceNum)}
    print('sent to webserver {}'.format(message))
    socket.send_json(message)

    # increment sliceNumber
    sliceNum += 1
    time.sleep(.1)
