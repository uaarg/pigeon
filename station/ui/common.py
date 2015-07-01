from PyQt5 import QtCore, QtWidgets, QtGui
import queue as queue_module

class BasePixmapLabel(QtWidgets.QLabel):
    """
    Base class for various Pixmap Label types. Features include:

    * Resizing the pixmap for display (in subclasses).
    * Mapping points on the displayed pixmap to points on the 
      original pixmap (and back).
    * Adding features to be displayed over the pixmap.
    """
    def __init__(self, *args, **kwargs):
        self.original_pixmap = kwargs.pop("pixmap", None)
        super().__init__(*args, **kwargs)

        self.features = []

    def _mapPointToOriginal(self, point):
        """
        Maps a point from the displayed pixmap to the original pixmap.
        Returns None if the point wasn't in the displayed pixmap.
        """
        border_x = self.width() - self.pixmap().width() # Accounting for 
        # extra space in the QLabel that doesn't have pixmap in it. Assuming
        # that the pixmap is centered horizontally. Not doing the same thing
        # for y because assuming pixmap is positioned at the top vertically.
       
        corrected_x = point.x() - border_x/2
        if not self.pixmap() or corrected_x < 0 or point.y() < 0 or corrected_x > self.pixmap().width() or point.y() > self.pixmap().height():
            return None
        else:
            return QtCore.QPoint(corrected_x / self.pixmap().width() * self.original_pixmap.width(), point.y() / self.pixmap().height() * self.original_pixmap.height())

    def _mapPointToDisplay(self, point):
        """
        Maps a point from the original pixmap to the displayed pixmap.
        Returns None if the point wasn't in the original pixmap.
        """
        border_x = self.width() - self.pixmap().width() # Accounting for 
        # extra space in the QLabel that doesn't have pixmap in it. Assuming
        # that the pixmap is centered horizontally. Not doing the same thing
        # for y because assuming pixmap is positioned at the top vertically.   
        if not self.pixmap() or point.x() < 0 or point.y() < 0 or point.x() > self.original_pixmap.width() or point.y() > self.original_pixmap.height():
            return None
        else:
            return QtCore.QPoint(point.x() * self.pixmap().width() / self.original_pixmap.width() + border_x/2, point.y() * self.pixmap().height() / self.original_pixmap.height())

    def pointOnOriginal(self, point):
        """
        Given a point on this widget's parent, returns a QPoint 
        object describing the location on the original pixmap (not 
        the scaled version) at this point.
        """
        return self._mapPointToOriginal(self.mapFromParent(point))

    def pointOnDisplay(self, point):
        """
        Given a point on the original pixmap, returns a QPoint
        object describing the location on this widget's parent.
        """
        return self.mapToParent(self._mapPointToDisplay(point))




    def _resize(self):
        self._positionFeatures()

    def _positionFeatures(self):
        """
        Reposition all the features so that they appear appear in the
        same place in the image.
        """
        features_removed = []
        for feature in self.features:
            try:
                feature.position()
            except RuntimeError: # The underlying C/C++ object can be deleted even if the python reference remains. Removing these features.
                features_removed.append(feature)

        for feature in features_removed:
            self.features.remove(feature)

    def addPixmapLabelFeature(self, feature):
        """
        Add the provided PixmapLabelFeature to this PixmapLabel.
        """
        # Giving the feature a function (not a method) that allows 
        # it to map a point on the original pixmap to the displayed
        # pixmap:
        def mapPoint(point):
            return self.pointOnDisplay(point)

        feature.mapPoint = mapPoint

        self.features.append(feature)


class PixmapLabel(BasePixmapLabel):
    """
    Provides a QLabel widget which automatically scales a pixmap 
    inserted into it. Keeps the pixmap's aspect ratio constant.
    """
    def _resize(self):
        if self.original_pixmap:
            super().setPixmap(self.original_pixmap.scaled(self.width(), self.height(), QtCore.Qt.KeepAspectRatio))
        super()._resize()

    def setPixmap(self, pixmap):
        self.original_pixmap = pixmap
        self._resize()

    def resizeEvent(self, resize_event):
        self._resize()

class WidthForHeightPixmapLabel(BasePixmapLabel):
    """
    Provies a QLabel widget which automatically demands the required 
    width needed to show it's pixmap at the provided height.
    """
    def _resize(self):
        if self.original_pixmap:
            pixmap = self.original_pixmap.scaledToHeight(self.height())
            self.setMinimumWidth(pixmap.width())
            super().setPixmap(pixmap)
        super()._resize()

    def setPixmap(self, pixmap):
        self.original_pixmap = pixmap
        self._resize()

    def resizeEvent(self, resize_event):
        self._resize()

class PixmapLabelMarker(QtWidgets.QLabel):
    """
    Class for markers (points) that can be put on a PixmapLabel
    (or anything that inherits from BasePixmapLabel).
    """
    def __init__(self, parent, icon, size=(20, 20)):
        super().__init__(parent)
        pixmap = QtGui.QPixmap(icon)
        self.setPixmap(pixmap)
        self.setScaledContents(True)
        self.hide()

        self.size = size
        self.point = None

        self.mapPoint = None # mapPoint is to be a function for mapping
        # a point on the PixmapLabel's original pixmap to the window.
        # It's set by the PixmapLabel that this PixmapLabelMarker is added
        # to becaues only the PixmapLabel knows how to do that mapping.

    def position(self):
        """
        Draw the marker at the position it's supposed to be at.
        """
        if not self.mapPoint:
            raise(Exception("Can't position a PixmapLabelMarker that hasn't been added to something yet."))
        if self.point:
            point = self.mapPoint(self.point)
            self.setGeometry(point.x()-self.size[0]/2, point.y() - self.size[1]/2, self.size[0], self.size[1])

    def moveTo(self, point):
        """
        Move the marker to the specified point on the parent PixmapLabel.
        """
        self.point = point
        self.position()


class BoldQLabel(QtWidgets.QLabel):
    """
    Bolding defined in the stylesheet.
    """

class ScaledListWidget(QtWidgets.QListWidget):
    """
    Provides a QListWidget which automatically scales...
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setFrameShape(QtWidgets.QFrame.NoFrame)
        
    def resizeEvent(self, resize_event):
        if self.Flow() == QtWidgets.QListWidget.LeftToRight:
            size = self.height()
        elif self.Flow() == QtWidgets.QListWidget.TopToBottom:
            size = self.width()
        else:
            raise(Exception("Unexpected flow encountered: %s. Expected %s or %s." % (self.Flow(), QtWidgets.QListWidget.LeftToRight, QtWidgets.QListWidget.TopToBottom)))
            
        self.setIconSize(QtCore.QSize(size, size))


class QueueMixin:
    """
    This is a mixin class that allows queues to be hooked up to slots.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.connected_queues = []

    def connectQueue(self, queue, slot):
        """
        Connects the provided queue to the specified slot:
        whenever a new element is added to the queue, the slot is called
        with it as an argument.
        """
        self.connected_queues.append((queue, slot))

    def _checkConnectedQueues(self):
        for queue, slot in self.connected_queues:
            try:
                value = queue.get(block=False)
            except queue_module.Empty:
                pass
            else:
                slot(value)

    def startQueueMonitoring(self):
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self._checkConnectedQueues)
        self.timer.start(100) # Time in milliseconds