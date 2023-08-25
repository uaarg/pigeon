import logging

from PyQt5 import QtCore, QtWidgets

translate = QtCore.QCoreApplication.translate

from ..common import WidthForHeightPixmapLabel, ListImageItem, ScaledListWidget


class ThumbnailArea(QtWidgets.QWidget):

    def __init__(self, *args, settings_data={}, minimum_height=60, **kwargs):
        super().__init__(*args, **kwargs)
        self.logger = logging.getLogger(__name__ + "." +
                                        self.__class__.__name__)
        self.settings_data = settings_data

        size_policy = QtWidgets.QSizePolicy(
            QtWidgets.QSizePolicy.MinimumExpanding,
            QtWidgets.QSizePolicy.Preferred)
        size_policy.setHorizontalStretch(10)
        size_policy.setVerticalStretch(10)
        self.setSizePolicy(size_policy)
        self.setMinimumSize(QtCore.QSize(200, minimum_height))

        self.setObjectName("thumbnail_area")
        self.layout = QtWidgets.QHBoxLayout(self)

        self.contents = ScaledListWidget()
        self.contents.setFlow(QtWidgets.QListWidget.LeftToRight)
        self.layout.addWidget(self.contents)

        self.recent_image = WidthForHeightPixmapLabel()
        self.layout.addWidget(self.recent_image)

        # self.setFrameShape(QtWidgets.QFrame.NoFrame)

        # self.title = QtWidgets.QLabel(self)
        # self.title.setText(translate("ThumbnailArea", "Thumbnail List"))

        self.images = []

    def addImage(self, image, index=None):
        if index:
            raise (NotImplementedError())

        item = ListImageItem(image.pixmap_loader, self.contents)
        item.image = image
        item.setToolTip(image.name)

        if self.settings_data.get("Follow Images", False):
            item.setSelected(True)
            self.contents.scrollToItem(item)

        self.logger.debug("Setting recent image pixmap")
        self.recent_image.setPixmap(image.pixmap_loader)
        self.recent_image.image = image
