#!/usr/bin/env python

from __future__ import print_function

import sys
from os import path, getenv

# if PAPARAZZI_SRC not set, then assume the tree containing this
# file is a reasonable substitute
# if PAPARAZZI_SRC not set, then assume the tree containing this file is a reasonable substitute
PPRZ_SRC = getenv("PAPARAZZI_SRC", path.normpath(path.join(path.dirname(path.abspath(__file__)), '~/paparazzi/')))

sys.path.append(PPRZ_SRC + "/sw/ext/pprzlink/lib/v1.0/python")

from pprzlink.ivy  import IvyMessagesInterface
from pprzlink.message   import PprzMessage

class CommandSender(object):
    def __init__(self, verbose=False, callback = None):
        self.verbose = verbose
        self.callback = callback
        self._interface = IvyMessagesInterface("SuasInterop", start_ivy=False)
        self._interface.subscribe(self.message_recv)
        self._interface.start()

    def message_recv(self, ac_id, msg):
        if (self.verbose and self.callback != None):
            self.callback(ac_id, msg)

    def shutdown(self):
        print("Shutting down ivy interface...")
        self._interface.shutdown()

    def __del__(self):
        self.shutdown()

    def add_shape_dict(self, status, obstacle_id, obmsg, color):
        msg = PprzMessage("ground", "SHAPE")
        msg['id'] = obstacle_id
        msg['color'] = color
        msg['status'] = 0 if status=="update" else 1
        msg['shape'] = int(obmsg.get("shape"))
        msg['lat1'] = int(obmsg.get("latitude1") * 10000000.)
        msg['lon1'] = int(obmsg.get("longitude1") * 10000000.)
        msg['lat2'] = int(obmsg.get("latitude2") * 10000000.)
        msg['lon2'] = int(obmsg.get("longitude2") * 10000000.)
        msg['lat3'] = int(obmsg.get("latitude3") * 10000000.)
        msg['lon3'] = int(obmsg.get("longitude3") * 10000000.)
        msg['lat4'] = int(obmsg.get("latitude4") * 10000000.)
        msg['lon4'] = int(obmsg.get("longitude4") * 10000000.)
        msg['radius'] = int(obmsg.get("sphere_radius") if "sphere_radius" in obmsg else obmsg.get("cylinder_radius"))
        msg['alt'] = int(obmsg.get("altitude_msl")*1000 if "altitude_msl" in obmsg else obmsg.get("cylinder_height") *1000)
        #print("Sending message: %s" % msg)
        self._interface.send(msg)
