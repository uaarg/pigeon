# Ruler class for measuring distance
from PyQt5 import QtCore, QtGui, QtWidgets
from geo import *

from ..common import PixmapLabel, PixmapLabelMarker
from ..ui import icons

from image import Image

class Ruler(QtCore.QObject):
    """
    Measures the real-world distance and angle between two points in a single Image.
    """
    ruler_updated = QtCore.pyqtSignal(int,str,str)
    def __init__(self, *args, **kwargs):
        super().__init__()
        self.num_clicks = 0
        self.firstinit = False
        self.distance = "None"
        self.angle = 0
        self.line = QtCore.QLine()

    def bindimagearea(self, imagearea):
        self.image_area = imagearea
        self.pixmap_label_markerSTR = []


    def click(self, image, point):
        self.num_clicks += 1
        if self.num_clicks == 1: # Odd click
            self.point1 = point
            self.line.setP1(point)  # Set new point
            self.showRuler(point,0)

        elif self.num_clicks == 2: # Even click
            self.point2 = point
            self.line.setP2(point) # set second point
            self.distance = image.distance([self.line.x1(), self.line.y1()],
                                      [self.line.x2(), self.line.y2()])
            self.angle = image.heading([self.line.x1(), self.line.y1()],
                                  [self.line.x2(), self.line.y2()])
            self.showRuler(point,1)

        elif self.num_clicks == 3: # Even click
            self.num_clicks = 0
            self.hideRuler()
            self.distance = "None"
            self.angle = 0
        self.ruler_updated.emit(self.num_clicks, str(self.distance),str(self.angle))

    def showRuler(self, point, ind):
        '''
        Used to draw the end icon of the Ruler
        '''
        #pixmap_label_markerSTR = str(point.x() + point.y())
        if self.firstinit == False:
            self.pixmap_label_markerSTR.append(PixmapLabelMarker(self.image_area, icons.ruler, offset=QtCore.QPoint(-9, -19)))
            if ind == 1:
                self.firstinit = True

        self.pixmap_label_markerSTR[ind] = PixmapLabelMarker(self.image_area, icons.ruler, offset=QtCore.QPoint(-9, -19))
        self.image_area.addPixmapLabelFeature(self.pixmap_label_markerSTR[ind])
        self.pixmap_label_markerSTR[ind].moveTo(point)

        self.pixmap_label_markerSTR[ind].show()

    def hideRuler(self):
        '''
        Hides the endpoints of the ruler when called
        '''
        for marker in self.pixmap_label_markerSTR:
            marker.hide()
