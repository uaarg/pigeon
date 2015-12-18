from PyQt5 import QtCore, QtWidgets, QtGui
import queue as queue_module
import sys
import logging

class BasePixmapLabel(QtWidgets.QLabel):
    """
    Base class for various Pixmap Label types. Features include:

    * Resizing the pixmap for display (in subclasses).
    * Mapping points on the displayed pixmap to points on the
      original pixmap (and back).
    * Adding features to be displayed over the pixmap.
    """
    def __init__(self, *args, pixmap_loader=None, **kwargs):
        self.logger = logging.getLogger(__name__ + "." + self.__class__.__name__)
        self.pixmap_loader = pixmap_loader
        if self.pixmap_loader:
            self.original_pixmap_width = pixmap_loader.width()
            self.original_pixmap_height = pixmap_loader.height()

        super().__init__(*args, **kwargs)

        self.features = []

    def _mapPointToOriginal(self, point):
        """
        Maps a point from the displayed pixmap to the original pixmap.
        Returns None if the point wasn't in the displayed pixmap.
        """
        if not self.pixmap():
            return None
        border_x = self.width() - self.pixmap().width() # Accounting for
        # extra space in the QLabel that doesn't have pixmap in it. Assuming
        # that the pixmap is centered horizontally. Not doing the same thing
        # for y because assuming pixmap is positioned at the top vertically.

        corrected_x = point.x() - border_x/2
        if not self.pixmap() or corrected_x < 0 or point.y() < 0 or corrected_x > self.pixmap().width() or point.y() > self.pixmap().height():
            return None
        else:
            return QtCore.QPoint(corrected_x / self.pixmap().width() * self.original_pixmap_width, point.y() / self.pixmap().height() * self.original_pixmap_height)

    def _mapPointToDisplay(self, point):
        """
        Maps a point from the original pixmap to the displayed pixmap.
        Returns None if the point wasn't in the original pixmap.
        """
        border_x = self.width() - self.pixmap().width() # Accounting for
        # extra space in the QLabel that doesn't have pixmap in it. Assuming
        # that the pixmap is centered horizontally. Not doing the same thing
        # for y because assuming pixmap is positioned at the top vertically.
        if not self.pixmap() or point.x() < 0 or point.y() < 0 or point.x() > self.original_pixmap_width or point.y() > self.original_pixmap_height:
            return None
        else:
            return QtCore.QPoint(point.x() * self.pixmap().width() / self.original_pixmap_width + border_x/2, point.y() * self.pixmap().height() / self.original_pixmap_height)

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

    def getPixmapForSize(self, size):
        """
        Mostly just a wrapper around PixmapLoader.getPixmapForSize().
        This method exists thought to avoid using the PixmapLoader
        if just a shrink is needed.
        """
        if not self.pixmap() or (size.width() > self.pixmap().width() or size.height() > self.pixmap().height()):
            return self.pixmap_loader.getPixmapForSize(size) # Need a bigger pixmap than the one we already have
        else:
            pixmap = self.pixmap().scaled(size, QtCore.Qt.KeepAspectRatio) # Just need to shrink our existing pixmap
            if pixmap.isNull():
                raise(Exception("Failed to scale pixmap to size %s, %s" % (size.width(), size.height())))
            return pixmap

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
        if self.pixmap_loader:
            super().setPixmap(self.getPixmapForSize(self.size()))
        super()._resize()

    def setPixmap(self, pixmap_loader):
        self.pixmap_loader = pixmap_loader
        self.original_pixmap_width = self.pixmap_loader.width()
        self.original_pixmap_height = self.pixmap_loader.height()
        self._resize()

    def resizeEvent(self, resize_event):
        self._resize()

class WidthForHeightPixmapLabel(BasePixmapLabel):
    """
    Provies a QLabel widget which automatically demands the required
    width needed to show it's pixmap at the provided height.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.logger = logging.getLogger(__name__ + "." + self.__class__.__name__)

    def _resize(self):
        if self.pixmap_loader:
            large_width = 50000
            pixmap = self.getPixmapForSize(QtCore.QSize(large_width, self.height())) # The large width value is a hack for infinity to get scale-to-height functionality
            self.setMinimumWidth(pixmap.width())
            super().setPixmap(pixmap)
        super()._resize()

    def setPixmap(self, pixmap_loader):
        self.pixmap_loader = pixmap_loader
        self.original_pixmap_width = self.pixmap_loader.width()
        self.original_pixmap_height = self.pixmap_loader.height()
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
        if pixmap.isNull():
            raise ValueError("Unable to load icon at %s." % icon)
        self.setPixmap(pixmap)
        self.setScaledContents(True)
        self.hide()

        self.size = size
        self.point = None

        self.mapPoint = None # mapPoint is to be a function for mapping
        # a point on the PixmapLabel's original pixmap to the window.
        # It's set by the PixmapLabel that this PixmapLabelMarker is added
        # to because only the PixmapLabel knows how to do that mapping.

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

class BaseQListWidget(QtWidgets.QListWidget):
    def iterItems(self):
        for i in range(self.count()):
            yield self.item(i)

class ScaledListWidget(BaseQListWidget):
    """
    Provides a QListWidget which automatically scales...
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setFrameShape(QtWidgets.QFrame.NoFrame)

        def on_scroll(*args, **kwargs):
            self._updateIconSizes()
        self.horizontalScrollBar().valueChanged.connect(on_scroll)

    def likelyVisibleItems(self):
        """
        Iterator for items which are probably visible.
        Analyses the scrolbar position and assumes that each item
        takes the same amount of space: not necessarily valid
        but should be close.
        """

        scrollbar = self.horizontalScrollBar()

        scrollbar_size = scrollbar.maximum() - scrollbar.minimum() + scrollbar.pageStep()
        if scrollbar_size:
            item_start = scrollbar.value() / scrollbar_size * self.count()
            item_end = (scrollbar.value() + scrollbar.pageStep()) / scrollbar_size * self.count()
        else:
            item_start = 0
            item_end = float("inf")

        for i in range(self.count()):
            if i >= item_start and i <= item_end:
                yield self.item(i)

    def _updateIconSizes(self):
        for item in self.likelyVisibleItems():
            item.updateIconSize()
            item.pixmap_loader.optimizeMemory()

    def resizeEvent(self, resize_event):
        size = self.calculateIconSize()
        self.setIconSize(size)

        self._updateIconSizes()


    def calculateIconSize(self):
        if self.Flow() == QtWidgets.QListWidget.LeftToRight:
            size = self.height()
        elif self.Flow() == QtWidgets.QListWidget.TopToBottom:
            size = self.width()
        else:
            raise(Exception("Unexpected flow encountered: %s. Expected %s or %s." % (self.Flow(), QtWidgets.QListWidget.LeftToRight, QtWidgets.QListWidget.TopToBottom)))
        return QtCore.QSize(size, size)

class ListImageItem(QtWidgets.QListWidgetItem):
    def __init__(self, pixmap_loader, list_widget):
        self.pixmap_loader = pixmap_loader
        icon = QtGui.QIcon(self.pixmap_loader.getPixmapForSize(list_widget.calculateIconSize()))
        super().__init__("", list_widget)
        self.setIcon(icon)

    def updateIconSize(self):
        icon = QtGui.QIcon(self.pixmap_loader.getPixmapForSize(self.listWidget().calculateIconSize()))
        self.setIcon(icon)

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

def format_duration_for_display(duration):
    if duration:
        return "%.0f s" % duration.total_seconds()
    else:
        return None