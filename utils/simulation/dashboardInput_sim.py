""" Tool to simulate the types of messages that Pyneal could send to the
dashboard.

This is useful for formatting and testing the appearance and behavior
of the dashboard

"""
import os
import time
import random

import json
import zmq
import numpy as np

### Configuration Settings
TR = 1
port = 5557
numTimepts = 60
maskPath = '/path/to/my/mask.nii.gz'
analysisChoice = 'Average'
volDims = '(64, 64, 44)'
outputPath = '/path/to/output/pyneal001'

# build the socket to send data to the dashboard webserver
print("Trying to connect to dashboard at: 127.0.0.1:{}".format(port))
context = zmq.Context.instance()
dashboardSocket = context.socket(zmq.REQ)
dashboardSocket.connect('tcp://127.0.0.1:{}'.format(port))


def sendToDashboard(topic=None, content=None):
    msg = {'topic': topic,
           'content': content}

    # send
    dashboardSocket.send_json(msg)
    print('sent: {}'.format(msg))

    response = dashboardSocket.recv_string()
    print('response: {}'.format(response))


# send initial settings to server
topic = 'configSettings'
content = {'mask': os.path.split(maskPath)[1],
           'analysisChoice': analysisChoice,
           'volDims': volDims,
           'numTimepts': numTimepts,
           'outputPath': outputPath}
sendToDashboard(topic=topic, content=content)

# continuously send new messages during 'scan'
for volIdx in range(numTimepts):
    startTime = time.time()

    #### send volume number
    sendToDashboard(topic='volIdx', content=volIdx)

    #### build motion params
    motionParams = {'volIdx': volIdx,
                    'rms_abs': np.random.normal(scale=2),
                    'rms_rel': np.random.normal(scale=.5)}
    sendToDashboard(topic='motion', content=motionParams)

    #### send timing parameters
    timingParams = {'volIdx': volIdx,
                    'processingTime': np.random.normal(scale=.14, loc=.4)}
    sendToDashboard(topic='timePerVol', content=timingParams)

    ### send pyneal scanner log update message
    newMsg = {'logString': ('Got vol idx:' + str(volIdx))}
    sendToDashboard(topic='pynealScannerLog', content=newMsg)

    #### send results server log update message
    requestMsg = {'type': 'request',
                  'logString': str(volIdx)}
    sendToDashboard(topic='resultsServerLog', content=requestMsg)

    serverResponse = {'foundResults': random.choice([True, False]),
                      'average': np.around(np.random.normal(loc=2432, scale=10), decimals=2)}
    responseMsg = {'type': 'response',
                   'logString': json.dumps(serverResponse),
                   'success': serverResponse['foundResults']}

    sendToDashboard(topic='resultsServerLog', content=responseMsg)

    # pause for TR
    elapsedTime = time.time() - startTime
    time.sleep(TR - elapsedTime)
