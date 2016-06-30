import threading
import sys
from os import path, getenv, system
from .ivylinker import CommandSender


PPRZ_SRC = getenv("PAPARAZZI_SRC", path.normpath(path.join(path.dirname(path.abspath(__file__)), '~/paparazzi/')))
PAPARAZZI_HOME = PPRZ_SRC
PAPARAZZI_SRC = PPRZ_SRC
sys.path.append(PPRZ_SRC + "/sw/ext/pprzlink/lib/v1.0/python")

class pprzMAP:
    def __init__(self):
        envvar = "export PAPARAZZI_HOME="+PAPARAZZI_SRC+";export PAPARAZZI_SRC="+PAPARAZZI_SRC
        system(envvar)
        self.ivylink = CommandSender(verbose=True)
        self.lastimgnum = None
        self.lastimgdat = None
        self.corner1 = None
        self.corner2 = None
        self.corner3 = None
        self.corner4 = None

    def start(self):
        self.gcsTH = threading.Thread(target = self.gcs)
        self.ivytcpTH2 = threading.Thread(target = self.tcpserver)
        self.ivytcpTH2.start()
        self.gcsTH.start()


    def tcpserver(self):
        system(PAPARAZZI_SRC+ "/sw/tools/tcp_aircraft_server/tcp_aircraft_server.py -b 127.255.255.255:2010")


    def gcs(self):
        system(PAPARAZZI_SRC+"/sw/ground_segment/cockpit/gcs -layout map_only.xml -b 127.255.255.255:2010")

    def draw_outline(self, image):
        outline = image.getImageOutline()
        self.corner1 = outline.positions[0].latLon()
        self.corner2 = outline.positions[1].latLon()
        self.corner3 = outline.positions[2].latLon()
        self.corner4 = outline.positions[3].latLon()

        pg = {
        'latitude1': self.corner1[0],
        'longitude1': self.corner1[1],
        'latitude2': self.corner2[0],
        'longitude2': self.corner2[1],
        'latitude3': self.corner3[0],
        'longitude3': self.corner3[1],
        'latitude4': self.corner4[0],
        'longitude4': self.corner4[1],
        'sphere_radius': 413,
        'altitude_msl': 139,
        'shape':1
        }

        if self.lastimgnum != None:
            self.ivylink.add_shape_dict("update",self.lastimgnum,self.lastimgdat,"red")

        self.ivylink.add_shape_dict("update",image.name,pg, "yellow")
        self.lastimgnum = image.name
        self.lastimgdat = pg

    def delete_all(self):
        for i in range(1,200):
            self.ivylink.add_shape_dict("delete",i,self.lastimgdat, "yellow")
