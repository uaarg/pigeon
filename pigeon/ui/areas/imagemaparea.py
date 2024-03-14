from PyQt6 import QtCore, QtWidgets

translate = QtCore.QCoreApplication.translate

from pigeon.ui.common import ImageArea

from pigeon.image import Image

class ImageMapArea(QtWidgets.QWidget):
    image_clicked = QtCore.pyqtSignal(Image, QtCore.QPoint)
    image_right_clicked = QtCore.pyqtSignal(Image, QtCore.QPoint)
    imageChanged = QtCore.pyqtSignal()

    def __init__(self, *args, settings_data={}, **kwargs):
        super().__init__(*args, **kwargs)
        self.settings_data = settings_data

        self.setObjectName("main_image_widget")
        
        size_policy = QtWidgets.QSizePolicy(
            QtWidgets.QSizePolicy.Policy.Ignored,
            QtWidgets.QSizePolicy.Policy.Ignored)
        size_policy.setHorizontalStretch(100)
        size_policy.setVerticalStretch(100)
        self.setSizePolicy(size_policy)
        self.setMinimumSize(QtCore.QSize(100, 100))

        main_layout = QtWidgets.QVBoxLayout(self)
        self.setLayout(main_layout)

        tab_widget = QtWidgets.QTabWidget()
        main_layout.addWidget(tab_widget)  

        image_tab = QtWidgets.QWidget()
        image_layout = QtWidgets.QVBoxLayout(image_tab)
        image_tab.setLayout(image_layout)  

        self.image_area = ImageArea(interactive=True)
        size_policy = QtWidgets.QSizePolicy(
            QtWidgets.QSizePolicy.Policy.Ignored,
            QtWidgets.QSizePolicy.Policy.Ignored)
        size_policy.setHorizontalStretch(100)
        size_policy.setVerticalStretch(100)
        self.image_area.setSizePolicy(size_policy)
        self.image_area.setMinimumSize(QtCore.QSize(50, 50))
        self.image_area.setAlignment(QtCore.Qt.AlignmentFlag.AlignHCenter)
        image_layout.addWidget(self.image_area)

        self.image = None

        map_tab = QtWidgets.QWidget()
        map_layout = QtWidgets.QVBoxLayout(map_tab)
        map_tab.setLayout(map_layout)

        tab_widget.addTab(map_tab, translate("ImageMapArea", "Map"))
        tab_widget.addTab(image_tab, translate("ImageMapArea", "Image"))

        tab_widget.setCurrentIndex(tab_widget.indexOf(map_tab))

        # Plumbline marker (if needed)
        self.plumbline = None
    
    def showImage(self, image):
        self.image = image
        self.image_area.setPixmap(image.pixmap_loader)
        self.imageChanged.emit()

    def getImage(self):
        """Gets the current image being displayed"""
        return self.image

    def mouseReleaseEvent(self, event):
        """
        Called by Qt when the user releases clicks on the image.

        Emitting an image_right_clicked event with the point if it was a
        right click.
        """
        try:
            point = QtCore.QPoint(event.x(), event.y())
            point = self.image_area.pointOnOriginal(point)
            if event.button() == QtCore.Qt.LeftButton and point:
                self.image_clicked.emit(self.image, point)
        except AttributeError:
            pass
