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

# decode response
serverResp = clientSocket.recv(1024)
serverResp = json.loads(serverResp.decode())
print('client received:')
print(type(serverResp))
print(serverResp)
