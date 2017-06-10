import threading
import sys
from os import path, getenv, system
from .ivylinker import ShapeSender


PPRZ_SRC = getenv("PAPARAZZI_SRC", path.normpath(path.join(path.dirname(path.abspath(__file__)), '~/paparazzi/')))
PIGEON_SRC = '~/pigeon/'
PAPARAZZI_HOME = PPRZ_SRC
PAPARAZZI_SRC = PPRZ_SRC
sys.path.append(PPRZ_SRC + "/sw/ext/pprzlink/lib/v1.0/python")

class pprzMAP:
    def __init__(self):
        envvar = "export PAPARAZZI_HOME="+PAPARAZZI_SRC+";export PAPARAZZI_SRC="+PAPARAZZI_SRC+";export PIGEON_SRC="+PIGEON_SRC
        system(envvar)
        self.ss = ShapeSender()
        
        self.lastlatarr = None
        self.lastlonarr = None
        self.currlatarr = None
        self.currlonarr = None


        self.lastarrexists = False

        self.corner1 = None
        self.corner2 = None
        self.corner3 = None
        self.corner4 = None

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

        self.ss.add_shape("update", 19, 1, "red", "blue", 100, self.lastlatarr, self.lastlonarr, "NULL", 0 )
        self.ss.add_shape("update", 21, 1, "yellow", "blue", 100, self.currlatarr, self.currlonarr, image.name, 0 )

    def shutDown(self):
        self.ss.add_shape("delete", 19, 1, "red", "blue", 100, self.lastlatarr, self.lastlonarr, "NULL", 1 )
        self.ss.add_shape("delete", 21, 1, "yellow", "blue", 100, self.currlatarr, self.currlonarr, "NULL", 1 )
        
