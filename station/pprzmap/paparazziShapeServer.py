import sys
import json
from os import path, getenv
import signal
from threading import Thread
from BaseHTTPServer import HTTPServer, BaseHTTPRequestHandler

PPRZ_SRC = getenv("PAPARAZZI_SRC", path.normpath(path.join(path.dirname(path.abspath(__file__)), '~/paparazzi/')))
sys.path.append(PPRZ_SRC + "/sw/ext/pprzlink/lib/v1.0/python")

from pprzlink.ivy  import IvyMessagesInterface
from pprzlink.message   import PprzMessage

class ShapeSender(object):
    def __init__(self, verbose=False):
        self.verbose = verbose
        self._interface = IvyMessagesInterface("ShapeSender", start_ivy=False)
        self._interface.start()

    def shutdown(self):
        self._interface.shutdown()

    def __del__(self):
        self.shutdown()

    def add_shape(self, payload):
        d = json.loads(payload)
        msg = PprzMessage("ground", "SHAPE")
        msg['id'] = d['id'] 
        msg['fillcolor'] = d['fillcolor']
        msg['linecolor'] = d['linecolor']
        msg['status'] = d['status']
        msg['shape'] = d['shape']
        msg['latarr'] = d['latarr']
        msg['lonarr'] = d['lonarr']
        msg['radius'] = d['radius']
        msg['text'] = d['text']
        msg['opacity'] = d['opacity']
        self._interface.send(msg)        
        
ss = ShapeSender()

class PUTHandler(BaseHTTPRequestHandler):
    def do_PUT(self):
        print "got shape"
        length = int(self.headers['Content-Length'])
        content = self.rfile.read(length)
        ss.add_shape(content)
        self.send_response(200)

def run_on(port):
    print("Starting a server on port %i" % port)
    server_address = ('10.42.0.220', port)
    httpd = HTTPServer(server_address, PUTHandler)
    httpd.serve_forever()

if __name__ == "__main__":
    ports = [int(arg) for arg in sys.argv[1:]]
    for port_number in ports:
        server = Thread(target=run_on, args=[port_number])
        server.daemon = True # Do not make us wait for you to exit
        server.start()
    signal.pause() # Wait for interrupt signal, e.g. KeyboardInterrupt

