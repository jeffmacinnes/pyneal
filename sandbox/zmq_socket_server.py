import zmq
import os
import numpy as np


port = 5555
host = '127.0.0.1'


context = zmq.Context.instance()
socket = context.socket(zmq.PAIR)
socket.bind('tcp://{}:{}'.format(host, port))

print('waiting for connection...')
while True:
    msg = socket.recv_string()
    print(msg)
    if msg[:4] == 'open':
        socket.send_string(msg)
        break

for a in range(10):
    matrixSize = np.random.randint(30,60)
    m = np.random.random((matrixSize, matrixSize))
    sliceHeader = {
        'dtype':str(m.dtype),
        'shape':m.shape,
        }

    ### Send data out the socket, listen for response
    socket.send_json(sliceHeader, zmq.SNDMORE) # header as json
    socket.send(m, flags=0, copy=False, track=False)

    scannerSocketResponse = socket.recv_string()
    print(scannerSocketResponse)





print('received connection...')
