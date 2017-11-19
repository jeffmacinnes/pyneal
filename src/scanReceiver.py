"""
Class to listen for incoming data from the scanner.

This tool is designed to be run in a separate thread, where it will:
    - establish a socket connection to pynealScanner (which will be sending slice
data from the scanner)
    - listen for incoming slice data (preceded by a header)
    - format the incoming data, and assign it to the proper location in a
    4D matrix for the entire san
In additiona, it also includes various methods for accessing the progress of an on-going scan, and returning data that has successfully arrived, etc.

--- Notes for setting up:
Socket Connection:
This tool uses the ZeroMQ library, instead of the standard python socket library.
ZMQ takes care of a lot of the backend work, is incredibily reliable, and offers
methods for easily sending pre-formatted types of data, including JSON dicts,
and numpy arrays.

Expectations for data formatting:
Once a scan has begun, this tool expects data to arrive over the socket
connection one slice at a time (though not necessarily in the proper
chronologic order).

There should be two parts to each slice transmission:
    1. First, a JSON header containing the following dict keys:
        - sliceIdx: within-volume index of the slice (0-based)
        - volIdx: volume index of the volume this slice belongs to (0-based)
        - sliceDtype: datatype of the slice pixel data (e.g. int16)
        - sliceShape: slice pixel dimensions (e.g. (64, 64))
    2. Next, the slice pixel data, as a string buffer.

Once both of those peices of data have arrived, this tool will send back a
confirmation string message.

Slice Orientation:
This tools presumes that arriving slices have been reoriented to RAS+
This is a critical premise for downstream analyses, so MAKE SURE the
slices are oriented in that way on the pynealScanner side before sending.
"""
# python2/3 compatibility
from __future__ import print_function

import os
import sys

import numpy as np





class scanReceiver(threading.Thread)
