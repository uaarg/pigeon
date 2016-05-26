from PyQt5 import QtCore, QtGui, QtWidgets
translate = QtCore.QCoreApplication.translate

from ..common import PixmapLabel, PixmapLabelMarker
from ..ui import icons

from image import Image
from features import Feature

class MainImageArea(QtWidgets.QWidget):
    image_clicked = QtCore.pyqtSignal(Image, QtCore.QPoint)
    image_right_clicked = QtCore.pyqtSignal(Image, QtCore.QPoint)
    featureChanged = QtCore.pyqtSignal(Feature)
    rightmousepresspoint = 0

    def __init__(self, *args, settings_data={}, features=[], **kwargs):
        super().__init__(*args, **kwargs)
        self.settings_data = settings_data
        self.features = features

        size_policy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Ignored, QtWidgets.QSizePolicy.Ignored)
        size_policy.setHorizontalStretch(100)
        size_policy.setVerticalStretch(100)
        self.setSizePolicy(size_policy)
        self.setMinimumSize(QtCore.QSize(100, 100))

        self.setObjectName("main_image_widget")

        self.layout = QtWidgets.QVBoxLayout(self)

        # self.title = QtWidgets.QLabel()
        # self.title.setText(translate("MainImageArea", "Main Image"))
        # self.title.setAlignment(QtCore.Qt.AlignHCenter)
        # self.layout.addWidget(self.title)

        self.image_area = PixmapLabel(interactive=True)
        size_policy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Ignored, QtWidgets.QSizePolicy.Ignored)
        size_policy.setHorizontalStretch(100)
        size_policy.setVerticalStretch(100)
        self.image_area.setSizePolicy(size_policy)
        self.image_area.setMinimumSize(QtCore.QSize(50, 50))
        self.image_area.setAlignment(QtCore.Qt.AlignHCenter)
        self.layout.addWidget(self.image_area)

        self.image = None

        # Plumbline marker (showing where directly below the plane is):
        self.plumbline = None

        # Features as drawn:
        self.feature_pixmap_label_markers = {}
        self.image_area.pixmap_label_marker_dropped.connect(self._moveFeatureById)

        self.ruler = QtCore.QLine()

    def updateRuler(self, image, point):
        if (self.ruler.dx() ==0 ) and (self.ruler.dy() == 0): # on first click
            print("Got to first click")
            self.ruler.setP1(point)  # Set new point
            print('Point 1 x = ' + str(point.x()) +'\n y = '+ str(point.y()))
            point.setX(point.x()+1) # Set changes to prep for second click
            point.setY(point.y()+1)
            print('Point 1 (+1,+1) x = ' + str(point.x()) +'\n y = '+ str(point.y()))
            self.ruler.setP2(point)
            print('dx = ' + str(self.ruler.dx()) +'\n dy = '+ str(self.ruler.dy()))
        elif (self.ruler.dx() == 1) and (self.ruler.dy() == 1): # on second click
            print('Got to second click')
            self.ruler.setP2(point) # set second point
            distance = image.distance([self.ruler.x1(), self.ruler.y1()],
                                      [self.ruler.x2(), self.ruler.y2()])
            #datPainter = QtGui.QPainter() # Probably need to add pixmap to this event, RJA, E.I.T.
            #datPainter.begin(self)
            #self._drawLine(datPainter, self.ruler, 'Ruler')
            #datPainter.end()
            print("Ruler is "+ str(distance)+ "m long.") # Add angle???
        self.showRuler(point)

    def showImage(self, image):
        self._clearFeatures()
        # clear past Ruler?
        self.image = image
        self.image_area.setPixmap(image.pixmap_loader)

        self._drawPlanePlumb()
        self._drawFeatures()

    def _drawPlanePlumb(self):
        """
        Draw a little plane icon on the image at the point directly
        below the plane. But only if this behaviour is enabled in the
        settings.
        """
        if not self.image:
            return

        if self.settings_data.get("Plane Plumbline", True):
            if not self.plumbline:
                self.plumbline = PixmapLabelMarker(self.image_area, icons.airplane)
                self.image_area.addPixmapLabelFeature(self.plumbline)

            pixel_x, pixel_y = self.image.getPlanePlumbPixel()
            if pixel_x and pixel_y:
                point = QtCore.QPoint(pixel_x, pixel_y)
                self.plumbline.moveTo(point)
                self.plumbline.show()
            else:
                self.plumbline.hide()

        elif self.plumbline:
            self.plumbline.hide()

    def _drawLine(self, datPainter, line, drwType ):
        '''
        This is the
        Used to draw the connecting line between any two points.
        '''

        if drwType == 'Ruler': # For the line of the ruler
            pen = QtGui.QPen(QtCore.Qt.red, 2, QtCore.Qt.DashDotDotLine)
        elif drwType == 'Border': # For the border of a Meta-Marker between markers
            pen = QtGui.QPen(QtCore.Qt.black, 2, QtCore.Qt.SolidLine)
        elif drwType == '':
            print('Type of Line is not supported!!')

        datPainter.setPen(pen)
        datPainter.drawLine(line.x1(), line.x2(), line.y1(), line.y2())

    def paintEvent(self, e):
        datPainter = QtGui.QPainter()
        datPainter.begin(self)
        self._drawLine(datPainter, self.ruler, 'Ruler')
        datPainter.end()

    def _clearFeatures(self):
        for pixmap_label_marker in self.feature_pixmap_label_markers.values():
            pixmap_label_marker.deleteLater()
        self.feature_pixmap_label_markers = {}

    def _drawFeature(self, feature):
        # Cleaning up any UI elements already drawn for this feature if they exist:
        old_pixmap_label_marker = self.feature_pixmap_label_markers.pop(feature.id(), None)
        if old_pixmap_label_marker:
            old_pixmap_label_marker.hide()

        if feature.position:
            pixel_x, pixel_y = self.image.invGeoReferencePoint(feature.position)
            if pixel_x and pixel_y:
                point = QtCore.QPoint(pixel_x, pixel_y)
                pixmap_label_marker = PixmapLabelMarker(self, icons.name_map[feature.icon_name], feature.icon_size, moveable=True, feature_id=feature.id())
                self.image_area.addPixmapLabelFeature(pixmap_label_marker)
                pixmap_label_marker.moveTo(point)
                pixmap_label_marker.setToolTip(str(feature))
                pixmap_label_marker.show()

                self.feature_pixmap_label_markers[feature.id()] = pixmap_label_marker


    def _drawFeatures(self):
        for feature in self.features:
            self._drawFeature(feature)

    def _moveFeatureById(self, feature_id, point):
        try:
            feature = [feature for feature in self.features if id(feature) == int(feature_id)][0]
        except IndexError:
            raise(Exception("Provided feature id of '%s' doesn't match any known features." % (feature_id,)))
        self._moveFeature(feature, point)

    def _moveFeature(self, feature, point):
        feature.updatePosition(self.image.geoReferencePoint(point.x(), point.y()))
        self._drawFeature(feature)
        self.featureChanged.emit(feature)

    def addFeature(self, feature):
        self._drawFeature(feature)

    def updateFeature(self, feature):
        self._drawFeature(feature)

    def showRuler(self, point):
        '''
        Used to draw the end icon of the Ruler
        '''
        pixmap_label_marker = PixmapLabelMarker(self.image_area, icons.end_point, offset=QtCore.QPoint(-9, -19))
        self.image_area.addPixmapLabelFeature(pixmap_label_marker)
        pixmap_label_marker.moveTo(point)
        #pixmap_label_marker.setToolTip(str(feature))
        pixmap_label_marker.show()

    def mouseReleaseEvent(self, event):
        """
        Called by Qt when the user clicks on the image.

        Emitting an image_right_clicked event with the point if it was a
        right click.
        """
        point = QtCore.QPoint(event.x(), event.y())
        point = self.image_area.pointOnOriginal(point)
        if event.button() == QtCore.Qt.LeftButton and point:
            self.image_clicked.emit(self.image, point)
        if event.button() == QtCore.Qt.RightButton and point:
            self.image_right_clicked.emit(self.image, point)