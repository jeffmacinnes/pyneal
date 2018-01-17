import socket
import json


# socket configs
port = 5556         # port number to connect to Pyneal over
host = '127.0.0.1'  # ip of where Pyneal is running


# connect to the results server of Pyneal
clientSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
clientSocket.connect((host, port))


# send request for volume number. Request must by 4-char string representing
# the volume number requested
request = '0004'
clientSocket.send(request.encode())

# When the results server recieved the request, it will send back a variable
# length response. But first, it will send a header indicating how long the response
# is. This is so the socket knows how many bytes to read
hdr = ''
while True:
    nextChar = clientSocket.recv(1).decode()
    if nextChar == '\n':
        break
    else:
        hdr += nextChar
msgLen = int(hdr)
print('message length: {}'.format(msgLen))

# now read the full response from the server
serverResp = clientSocket.recv(msgLen)

# format at JSON
serverResp = json.loads(serverResp.decode())
print('client received:')
print(serverResp)
