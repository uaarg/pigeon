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
        self.distance = 0
        self.angle = 0
        self.line = QtCore.QLine()
        self.draggable = False
        self.num_clicks = 0

    def bindimagearea(self, imagearea):
        self.image_area = imagearea
        self.pixmap_label_marker_1 = None
        self.pixmap_label_marker_2 = None
        self.pixmap_label_text = None
        self.initPoints()

    def initPoints(self):
        self.pixmap_label_marker_1 = PixmapLabelMarker(self.image_area, icons.ruler, offset=QtCore.QPoint(-9, -19))
        self.pixmap_label_marker_2 = PixmapLabelMarker(self.image_area, icons.ruler, offset=QtCore.QPoint(-9, -19))

        self.image_area.addPixmapLabelFeature(self.pixmap_label_marker_1)
        self.image_area.addPixmapLabelFeature(self.pixmap_label_marker_2)

        self.rulertext = PixmapLabelMarker(self.image_area, icons.airplane, size=(150, 20), id_="its aruler", isruler=True)
        self.rulertext.setStyleSheet("QLabel {background-color: white;}")
        self.image_area.addPixmapLabelFeature(self.rulertext)

    def press(self, image, point):
        if self.num_clicks == 0:
            self.draggable = True
            self.point1 = point
            self.line.setP1(point)  # Set new point
            self.pixmap_label_marker_1.moveTo(self.point1)
            self.pixmap_label_marker_1.show()
            self.num_clicks = 1
            return
        if self.num_clicks == 1:
            self.num_clicks = 2
            return
        if self.num_clicks == 2:
            self.clear()
            self.num_clicks = 0
            return


    def release(self, image, point):
        self.draggable = False
        if self.num_clicks == 2:
            self.calc(image,point)
            self.num_clicks = 2
            return

    def move(self, image, point):
        num_clicks = 2
        self.calc(image, point)

    def calc(self, image, point):
        self.pixmap_label_marker_2.moveTo(point)
        self.pixmap_label_marker_2.show()
        self.point2 = point
        self.line.setP2(point) # set second point
        self.distance = image.distance([self.line.x1(), self.line.y1()],
                                  [self.line.x2(), self.line.y2()])
        self.angle = image.heading([self.line.x1(), self.line.y1()],
                              [self.line.x2(), self.line.y2()])
        self.rulertext.setText("Dist:" + str("{0:.2f}".format(self.distance)) + " Angl:" + str("{0:.2f}".format(self.angle)))
        self.rulertext.moveTo(point)
        self.rulertext.show()
        self.calculated = True

    def clear(self):
        self.pixmap_label_marker_1.hide()
        self.pixmap_label_marker_2.hide()
        self.rulertext.hide()
        self.angle = 0;
        self.distance = 0;
