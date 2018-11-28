""" Tool to simulate and demo how an end-user may request results from Pyneal
during a real-time scan.

In a neurofeedback context, for example, the end-user may be the software that
is controlling the experimental task. In this case, anytime the task wants to
present feedback to the participant, it must request the output of the
real-time analysis for a specific set of timepoints (or volumes).

This is an example of how requests should be formatted and sent to Pyneal.
Requests are made on a per-volume basis, and each request should take the form
of a 4-character string representing the desired volume index (using a 0-based
index). For example, to request the first volume in the series, the string
would be '0000'; to request the 25th volume in the series the string would be
'0024', and so on...

Pyneal will send back a response comprised of two parts: first a header, and
then followed by the results. The results message contains all of the analysis
results that were calculated for that volume; since different analyses can
yield differing numbers of results, the length of the results message can vary
considerably. That is why we include the header, which is a short message
simply telling the end-user how many bytes to expect for the full message.

The results message starts off as a python dictionary, and then converted to
JSON and encoded as a byte array before sending over the socket. The end-user
should reencode the byte array as a JSON object in order to access the results.
At a minumum each results message will contain an entry called 'foundResults'
that stores a boolean value indicating whether Pyneal has a result for this
volume (True) or not (False). If 'foundResults' is True, there will also be
additional entries containing the results for that volume. How those results
are formatted and named depends on the analysis option chosen. For instance,
for basic ROI averaging, the results may look like 'average':1423, indicating
the ROI had an average value of 1423 on this volume.

Usage
-----
python endUser_sim.py [-sh] [-sp] volIdx

e.g. python endUser_sim.py 24

Parameters
----------
volIdx : int
    the index (0-based) of the volume you'd like to request results from
sh : string, optional
    i.p. address of the result server. defaults to 127.0.0.1
sp : port, optional
    port number to use for communication with result server. defaults to 5556

Returns
-------
The returned result from the Pyneal Result server will be printed to stdOut

"""
import argparse
import socket
import json
import sys


def requestResult(host, port, volIdx):
    """ send request to pyneal results server for specific result

    Parameters
    ----------
    volIdx : int
        the index (0-based) of the volume you'd like to request results from
    host : string
        i.p. address of the result server
    port : int
        port number to use for communication with result server

    """
    # connect to the results server of Pyneal
    clientSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    clientSocket.connect((host, port))

    # send request for volume number. Request must by 4-char string representing
    # the volume number requested
    request = str(volIdx).zfill(4)

    print('Sending request to {}:{} for vol {}'.format(host, port, request))
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

    # now read the full response from the server
    serverResp = clientSocket.recv(msgLen)

    # format at JSON
    serverResp = json.loads(serverResp.decode())
    print('client received:')
    print(serverResp)

    clientSocket.close()

if __name__ == '__main__':
    # parse arguments
    parser = argparse.ArgumentParser()
    parser.add_argument('-sh', '--socketHost',
                        default='127.0.0.1',
                        type=str,
                        help='Pyneal Result Server host')
    parser.add_argument('-sp', '--socketPort',
                        default=5556,
                        type=int,
                        help='Pyneal Result Server port')
    parser.add_argument('volIdx')
    args = parser.parse_args()

    requestResult(args.socketHost, args.socketPort, args.volIdx)
