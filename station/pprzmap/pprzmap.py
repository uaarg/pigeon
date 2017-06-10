import threading
import sys
from os import path, getenv, system
from .ivylinker import CommandSender


PPRZ_SRC = getenv("PAPARAZZI_SRC", path.normpath(path.join(path.dirname(path.abspath(__file__)), '~/paparazzi/')))
PIGEON_SRC = '~/pigeon/'
PAPARAZZI_HOME = PPRZ_SRC
PAPARAZZI_SRC = PPRZ_SRC
sys.path.append(PPRZ_SRC + "/sw/ext/pprzlink/lib/v1.0/python")

class pprzMAP:
    def __init__(self):
        envvar = "export PAPARAZZI_HOME="+PAPARAZZI_SRC+";export PAPARAZZI_SRC="+PAPARAZZI_SRC+";export PIGEON_SRC="+PIGEON_SRC
        system(envvar)
        self.ivylink = CommandSender(verbose=True)
        
        self.lastlatarr = None
        self.lastlonarr = None
        self.currlatarr = None
        self.currlonarr = None


        self.lastarrexists = False

        self.corner1 = None
        self.corner2 = None
        self.corner3 = None
        self.corner4 = None

    def start(self):
        pass
        #self.gcsTH = threading.Thread(target = self.gcs)
        #self.ivytcpTH2 = threading.Thread(target = self.tcpserver)
        #self.ivytcpTH2.start()
        #self.gcsTH.start()


    def tcpserver(self):
        system(PAPARAZZI_SRC+ "/sw/tools/tcp_aircraft_server/tcp_aircraft_server.py -b 127.255.255.255:2010")

    def gcs(self):
        system(PIGEON_SRC+ "/station/pprzmap/gcs -layout map_only.xml -b 127.255.255.255:2010")

    def draw_outline(self, image):
        self.lastlatarr = self.currlatarr
        self.lastlonarr = self.currlonarr

        outline = image.getImageOutline()
        self.corner1 = outline.positions[0].latLon()
        self.corner2 = outline.positions[1].latLon()
        self.corner3 = outline.positions[2].latLon()
        self.corner4 = outline.positions[3].latLon()

        self.currlatarr = [self.corner1[0], self.corner2[0],self.corner3[0],self.corner4[0]]
        self.currlonarr = [self.corner1[1], self.corner2[1],self.corner3[1],self.corner4[1]]

        if not self.lastarrexists:
            self.lastarrexists = True
            self.lastlatarr = self.currlatarr
            self.lastlonarr = self.currlonarr

        self.ivylink.add_shape("update", 19, 1, "red", "blue", 100, self.lastlatarr, self.lastlonarr, "NULL", 1 )
        self.ivylink.add_shape("update", 21, 1, "yellow", "blue", 100, self.currlatarr, self.currlonarr, image.name, 1 )

    def delete_all(self):
        self.ivylink.add_shape("delete", 19, 1, "red", "blue", 100, self.lastlatarr, self.lastlonarr, "NULL", 1 )
        self.ivylink.add_shape("delete", 21, 1, "yellow", "blue", 100, self.currlatarr, self.currlonarr, "NULL", 1 )
        
    def shutDown(self):
        self.delete_all()
        self.ivylink.shutdown()

