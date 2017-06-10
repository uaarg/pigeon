#!/usr/bin/env python

from __future__ import print_function

import sys
from os import path, getenv
import requests

# if PAPARAZZI_SRC not set, then assume the tree containing this
# file is a reasonable substitute
# if PAPARAZZI_SRC not set, then assume the tree containing this file is a reasonable substitute
PPRZ_SRC = getenv("PAPARAZZI_SRC", path.normpath(path.join(path.dirname(path.abspath(__file__)), '~/paparazzi/')))

sys.path.append(PPRZ_SRC + "/sw/ext/pprzlink/lib/v1.0/python")

from pprzlink.ivy  import IvyMessagesInterface
from pprzlink.message   import PprzMessage

class ShapeSender(object):
    def add_shape(self, status, obstacle_id, shape, linecolor, fillcolor, radius, latarr, lonarr, text, opacity ):
        msg = PprzMessage("ground", "SHAPE")
        lonarr = [int(lon * 1e7) for lon in lonarr]
        latarr = [int(lon * 1e7) for lon in latarr]
        msg['id'] = obstacle_id
        msg['fillcolor'] = fillcolor
        msg['linecolor'] = linecolor
        msg['status'] = 0 if status=="update" else 1
        msg['shape'] = shape
        msg['latarr'] = latarr
        msg['lonarr'] = lonarr
        msg['radius'] = int(radius)
        msg['text'] = text
        msg['opacity'] = opacity
        try:
            r = requests.put("http://10.42.0.220:1919", timeout= 0.00001, data = msg.to_json())
        except:
            pass
