import socket

port = 5556

clientSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

clientSocket.connect(('127.0.0.1', port))

clientSocket.send('hi from client'.encode())
serverResp = clientSocket.recv(1024).decode()
print('client received: {}'.format(serverResp))
