from PyQt5 import QtCore, QtWidgets
import queue as queue_module

class PixmapLabel(QtWidgets.QLabel):
    """
    Provides a QLabel widget which automatically scales a pixmap 
    inserted into it. Keeps the pixmap's aspect ratio constant.
    """
    def __init__(self, *args, **kwargs):
        self.pixmap = kwargs.pop("pixmap", None)
        super().__init__(*args, **kwargs)

    def __resize(self):
        if self.pixmap:
            super().setPixmap(self.pixmap.scaled(self.width(), self.height(), QtCore.Qt.KeepAspectRatio))

    def setPixmap(self, pixmap):
        self.pixmap = pixmap
        self.__resize()

    def resizeEvent(self, resize_event):
        self.__resize()


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