import socket
import json

port = 5556

# connect to server
clientSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
clientSocket.connect(('127.0.0.1', port))


# send request
request = json.dumps({'volume':25})
request = '0004'
clientSocket.send(request.encode())

# read header
hdr = ''
while True:
    nextChar = clientSocket.recv(1).decode()
    print(nextChar)
    if nextChar == '\n':
        break
    else:
        hdr += nextChar
print(hdr)
msgLen = int(hdr)
print('message length: {}'.format(msgLen))

# now read the message
serverResp = clientSocket.recv(msgLen)
serverResp = json.loads(serverResp.decode())
print('client received:')
print(serverResp)
