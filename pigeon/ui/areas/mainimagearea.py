from PyQt6 import QtCore, QtWidgets

translate = QtCore.QCoreApplication.translate

from pigeon.ui.common import PixmapLabel, PixmapLabelMarker
from pigeon.ui import icons

from pigeon.image import Image
from pigeon.features import Feature

from pigeon.ui.areas.ruler import Ruler


class MainImageArea(QtWidgets.QWidget):
    image_clicked = QtCore.pyqtSignal(Image, QtCore.QPoint)
    image_right_clicked = QtCore.pyqtSignal(Image, QtCore.QPoint)
    featureChanged = QtCore.pyqtSignal(Feature)
    imageChanged = QtCore.pyqtSignal()

    def __init__(self, *args, settings_data={}, features=[], **kwargs):
        super().__init__(*args, **kwargs)
        self.settings_data = settings_data
        self.features = features

        size_policy = QtWidgets.QSizePolicy(
            QtWidgets.QSizePolicy.Policy.Ignored,
            QtWidgets.QSizePolicy.Policy.Ignored)
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
        size_policy = QtWidgets.QSizePolicy(
            QtWidgets.QSizePolicy.Policy.Ignored,
            QtWidgets.QSizePolicy.Policy.Ignored)
        size_policy.setHorizontalStretch(100)
        size_policy.setVerticalStretch(100)
        self.image_area.setSizePolicy(size_policy)
        self.image_area.setMinimumSize(QtCore.QSize(50, 50))
        self.image_area.setAlignment(QtCore.Qt.AlignmentFlag.AlignHCenter)
        self.layout.addWidget(self.image_area)

        self.image = None

        # Plumbline marker (showing where directly below the plane is):
        self.plumbline = None

        # Features as drawn:
        self.feature_pixmap_label_markers = {}
        self.image_area.pixmap_label_marker_dropped.connect(
            self._moveFeatureById)

        self.ruler = Ruler()
        self.ruler.bindimagearea(self.image_area)

    def showImage(self, image):
        self._clearFeatures()
        # clear past Ruler?
        self.image = image
        self.image_area.setPixmap(image.pixmap_loader)

        self._drawPlanePlumb()
        self._drawFeatures()
        self.imageChanged.emit()

    def getImage(self):
        """Gets the current image being displayed"""
        return self.image

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
                self.plumbline = PixmapLabelMarker(self.image_area,
                                                   icons.airplane)
                self.image_area.addPixmapLabelFeature(self.plumbline)

            pixel_x, pixel_y = self.image.getPlanePlumbPixel()
            if False and pixel_x and pixel_y:
                point = QtCore.QPoint(pixel_x, pixel_y)
                self.plumbline.moveTo(point)
                self.plumbline.show()
            else:
                self.plumbline.hide()

        elif self.plumbline:
            self.plumbline.hide()

    def _clearFeatures(self):
        for pixmap_label_marker in self.feature_pixmap_label_markers.values():
            pixmap_label_marker.deleteLater()
        self.feature_pixmap_label_markers = {}

    def _drawFeature(self, feature):
        if not self.image:
            return  # Don't need to draw anything if we don't have an image to draw on

        if feature.id in [
                feature.id for feature in self.features
        ]:  # Only drawing top-level features, not subfeatures
            for feature_point in feature.visiblePoints(self.image):
                # Cleaning up any UI elements already drawn for this feature if they exist:
                old_pixmap_label_marker = self.feature_pixmap_label_markers.pop(
                    feature_point.id, None)
                if old_pixmap_label_marker:
                    old_pixmap_label_marker.hide()

                pixel_x, pixel_y = feature_point.point_on_image
                if False and pixel_x and pixel_y:
                    point = QtCore.QPoint(pixel_x, pixel_y)
                    pixmap_label_marker = PixmapLabelMarker(
                        self,
                        icons.name_map[feature_point.icon_name],
                        feature_point.icon_size,
                        moveable=True,
                        id_=feature_point.id)
                    self.image_area.addPixmapLabelFeature(pixmap_label_marker)
                    pixmap_label_marker.moveTo(point)
                    pixmap_label_marker.setToolTip(str(feature))
                    pixmap_label_marker.show()

                    self.feature_pixmap_label_markers[
                        feature_point.id] = pixmap_label_marker

    def _drawFeatures(self):
        for feature in self.features:
            self._drawFeature(feature)

    def _moveFeatureById(self, id_, point):
        for feature in self.features:
            result = feature.updatePointById(id_, self.image,
                                             (point.x(), point.y()))
            if result:
                self._moveFeature(feature, point)
                break
        else:
            raise (Exception(
                "Provided id of '%s' doesn't match any known features." %
                (id_, )))

    def _moveFeature(self, feature, point):
        feature.updatePoint(self.image, (point.x(), point.y()))
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
        pixmap_label_marker = PixmapLabelMarker(self.image_area,
                                                icons.end_point,
                                                offset=QtCore.QPoint(-9, -19))
        self.image_area.addPixmapLabelFeature(pixmap_label_marker)
        pixmap_label_marker.moveTo(point)
        #pixmap_label_marker.setToolTip(str(feature))
        pixmap_label_marker.show()

    def mousePressEvent(self, event):
        """
        Called by Qt when the user clicks on the image.

        Emitting an image_right_clicked event with the point if it was a
        right click.
        """
        if event.button() == QtCore.Qt.MouseButton.RightButton:
            point = QtCore.QPoint(event.x(), event.y())
            point = self.image_area.pointOnOriginal(point)
            if point:
                self.ruler.press(self.image, point)

    def mouseReleaseEvent(self, event):
        """
        Called by Qt when the user releases clicks on the image.

        Emitting an image_right_clicked event with the point if it was a
        right click.
        """
        point = QtCore.QPoint(event.x(), event.y())
        point = self.image_area.pointOnOriginal(point)
        if event.button() == QtCore.Qt.LeftButton and point:
            self.image_clicked.emit(self.image, point)
        if event.button() == QtCore.Qt.RightButton and point:
            self.ruler.release(self.image, point)

    def mouseMoveEvent(self, event):
        if self.ruler.draggable:
            point = QtCore.QPoint(event.x(), event.y())
            point = self.image_area.pointOnOriginal(point)
            if point:
                self.ruler.move(self.image, point)
