import zmq
import tmpModule as tmp
import time


context = zmq.Context.instance()
socket = context.socket(zmq.REP)
socket.bind('tcp://127.0.0.1:80101')

tmp.callThisFunction(socket)


clientSocket = context.socket(zmq.REQ)
clientSocket.connect('tcp://127.0.0.1:80101')
clientSocket.send_string('hello')

time.sleep(2)
