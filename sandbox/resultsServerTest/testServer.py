import zmq


context = zmq.Context()

port = 6666

# define the socket using the context
serverSocket = context.socket(zmq.REP)
serverSocket.bind("tcp://127.0.0.1:{}".format(port))


while True:
    message = serverSocket.recv()
    print('server got message: {}'.format(message))
    serverSocket.send_string('got it')
