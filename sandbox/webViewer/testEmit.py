import zmq
import sys
import time
import random

port = '5556'

# set up publish port
context = zmq.Context()
socket = context.socket(zmq.PUB)
socket.bind("tcp://127.0.0.1:5556")

while True:
    topic = 'testTopic'
    message = str(random.choice([1,2]))
    print('topic: {}, msg: {}'.format(topic, message))
    socket.send_string(message)
    time.sleep(1)
