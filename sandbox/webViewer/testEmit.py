import zmq
import sys
import time
import random

port = '5556'

# set up publish port
context = zmq.Context()
socket = context.socket(zmq.PUB)
socket.bind("tcp://127.0.0.1:5556")

socket.send_string('open')


sliceNum = 0
while True:
    topic = 'testTopic'
    message = str(sliceNum)
    print('sent: topic: {}, msg: {}'.format(topic, message))
    socket.send_string(message)

    # increment sliceNumber
    sliceNum += 1
    time.sleep(.1)
