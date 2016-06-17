# Ruler class for measuring distance
from PyQt5 import QtCore, QtGui, QtWidgets
from geo import *

from ..common import PixmapLabel, PixmapLabelMarker
from ..ui import icons

from image import Image

class Ruler(QtCore.QLine):
    """
    Measures the real-world distance and angle between two points in a single Image.
    """

    def __init__(self, *args, **kwargs):
        super().__init__()
        self.num_clicks = 0
        self.firstinit = False


    def bindimagearea(self, imagearea):
        self.image_area = imagearea
        self.pixmap_label_markerSTR = []


    def click(self, image, point):
        self.num_clicks += 1
        if self.num_clicks == 1: # Odd click
            self.point1 = point
            self.setP1(point)  # Set new point
            self.showRuler(point,0)

        elif self.num_clicks == 2: # Even click
            self.point2 = point
            self.setP2(point) # set second point
            distance = image.distance([self.x1(), self.y1()],
                                      [self.x2(), self.y2()])
            angle = image.heading([self.x1(), self.y1()],
                                  [self.x2(), self.y2()])
            print("Distance: {:f} m, Angle: {:f} degrees".format(distance, angle))
            self.showRuler(point,1)

        elif self.num_clicks == 3: # Even click
            self.num_clicks = 0
            self.hideRuler()

    def showRuler(self, point, ind):
        '''
        Used to draw the end icon of the Ruler
        '''
        #pixmap_label_markerSTR = str(point.x() + point.y())
        if self.firstinit == False:
            self.pixmap_label_markerSTR.append(PixmapLabelMarker(self.image_area, icons.end_point, offset=QtCore.QPoint(-9, -19)))
            if ind == 1:
                self.firstinit = True

        self.pixmap_label_markerSTR[ind] = PixmapLabelMarker(self.image_area, icons.end_point, offset=QtCore.QPoint(-9, -19))
        self.image_area.addPixmapLabelFeature(self.pixmap_label_markerSTR[ind])
        self.pixmap_label_markerSTR[ind].moveTo(point)

        self.pixmap_label_markerSTR[ind].show()

    def hideRuler(self):
        '''
        Hides the endpoints of the ruler when called
        '''
        for marker in self.pixmap_label_markerSTR:
            marker.hide()
