#!/usr/bin/env python3

import sys
import logging
import datetime

from PyQt5 import QtCore, QtGui, QtWidgets
translate = QtCore.QCoreApplication.translate

from image import Image

from .common import PixmapLabel, WidthForHeightPixmapLabel, PixmapLabelMarker, BoldQLabel, ScaledListWidget, QueueMixin
from .style import stylesheet
from ui import icons

logger = logging.getLogger(__name__)

THUMBNAIL_AREA_START_HEIGHT = 100
THUMBNAIL_AREA_MIN_HEIGHT = 50
INFO_AREA_MIN_WIDTH = 250
MARKER_AREA_MIN_WIDTH = 250

class UI(QueueMixin):
    """
    Class for the rest of the application to interface with the UI. 

    This implementation of the class uses PyQt5 to provide the UI but
    theoretically, other frameworks could be used without the rest of 
    the application caring, as long as this class's API is 
    implemented. Or, more likely: a mock UI instance could be used in
    unit testing for easy testing of the rest of the application.
    """
    def __init__(self, save_settings, load_settings, image_queue, ground_control_points=[]):
        super().__init__()
        self.settings_data = load_settings()

        self.app = QtWidgets.QApplication(sys.argv)
        self.app.setStyleSheet(stylesheet)
        self.main_window = MainWindow(self.settings_data, ground_control_points)

        self.main_window.info_area.settings_area.settings_load_requested.connect(lambda: self.main_window.info_area.settings_area.setSettings(load_settings()))
        self.main_window.info_area.settings_area.settings_save_requested.connect(save_settings)

        self.connectQueue(image_queue, self.addImage)

        def print_image_clicked(image, point):
            string = "Point clicked in image %s: %s" % (image.name, image.geoReferencePoint(point.x(), point.y()))
            print(string)
            logger.info(string)

        self.main_window.main_image_area.image_right_clicked.connect(print_image_clicked)
        self.main_window.main_image_area.image_clicked.connect(print_image_clicked)

    def run(self):
        self.main_window.info_area.settings_area.settings_load_requested.emit()
        self.main_window.show()
        self.startQueueMonitoring()
        return self.app.exec_()

    def addImage(self, image):
        self.main_window.addImage(image)
        

class MainWindow(QtWidgets.QMainWindow):
    def __init__(self, settings_data={}, ground_control_points=[]):
        super().__init__()
        self.settings_data = settings_data

        # State
        self.current_image = None

        # Defining window properties
        self.setObjectName("main_window")
        self.showMaximized()
        self.setMinimumSize(QtCore.QSize(500, 500))
        size_policy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        size_policy.setHorizontalStretch(1)
        size_policy.setVerticalStretch(1)
        self.setSizePolicy(size_policy)
        self.setWindowTitle(translate("MainWindow", "Ground Imaging Station"))

        # Defining the page layout
        self.central_widget = QtWidgets.QWidget(self)
        self.central_widget.setObjectName("central_widget")        
        self.setCentralWidget(self.central_widget)
        self.grid_layout = QtWidgets.QGridLayout(self.central_widget)
        self.grid_layout.setObjectName("grid_layout")

        self.main_vertical_split = QtWidgets.QSplitter()
        self.main_vertical_split.setOrientation(QtCore.Qt.Vertical)
        self.main_vertical_split.setObjectName("main_vertical_split")
        self.grid_layout.addWidget(self.main_vertical_split, 0, 0, 1, 1)

        self.main_horizontal_split = QtWidgets.QSplitter(self.main_vertical_split)
        self.main_horizontal_split.setOrientation(QtCore.Qt.Horizontal)
        self.main_horizontal_split.setObjectName("main_horizontal_split")
        size_policy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.MinimumExpanding, QtWidgets.QSizePolicy.Preferred)
        size_policy.setHorizontalStretch(0)
        size_policy.setVerticalStretch(100)
        self.main_horizontal_split.setSizePolicy(size_policy)
        self.main_horizontal_split.setMinimumSize(QtCore.QSize(200, THUMBNAIL_AREA_START_HEIGHT))

        # Populating the page layout with the major components.
        self.info_area = InfoArea(self.main_horizontal_split, settings_data=settings_data)
        self.main_image_area = MainImageArea(self.main_horizontal_split, settings_data=settings_data, ground_control_points=ground_control_points)
        self.marker_area = MarkerArea(self.main_horizontal_split)
        self.thumbnail_area = ThumbnailArea(self.main_vertical_split, settings_data=settings_data)

        # Hooking up some inter-component benhaviour
        self.thumbnail_area.contents.currentItemChanged.connect(lambda new_item, old_item: self.showImage(new_item.image)) # Show the image that's selected

        # # Defining the menu bar, status bar, and toolbar. These aren't used yet.
        # self.menubar = QtWidgets.QMenuBar(self)
        # self.menubar.setGeometry(QtCore.QRect(0, 0, 689, 21))
        # self.menubar.setDefaultUp(False)
        # self.menubar.setObjectName("menubar")
        # self.setMenuBar(self.menubar)
        # self.statusbar = QtWidgets.QStatusBar(self)
        # self.statusbar.setObjectName("statusbar")
        # self.setStatusBar(self.statusbar)
        # self.toolBar = QtWidgets.QToolBar(self)
        # self.toolBar.setObjectName("toolBar")
        # self.addToolBar(QtCore.Qt.TopToolBarArea, self.toolBar)

        # Finishing up
        QtCore.QMetaObject.connectSlotsByName(self)

    def addImage(self, image):
        image.pixmap = QtGui.QPixmap(image.path) # Storing the pixmap in the image
        if image.pixmap.isNull():
            raise(ValueError("Failed to load image at %s" % image.path))

        # Recording the width and height of the image for other code to use: 
        image.width = image.pixmap.width()
        image.height = image.pixmap.height()

        if self.settings_data.get("Follow Images", False) or not self.current_image:
            self.showImage(image)
        self.thumbnail_area.addImage(image)
        self.info_area.addImage(image)

    def setSettings(self, settings_data):
        return self.info_area.setSettings(settings_data)

    def showImage(self, image):
        self.current_image = image
        self.main_image_area.showImage(image)
        self.info_area.showImage(image)

class InfoArea(QtWidgets.QFrame):
    def __init__(self, *args, settings_data={}, **kwargs):
        super().__init__(*args, **kwargs)

        size_policy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.MinimumExpanding)
        size_policy.setHorizontalStretch(0)
        size_policy.setVerticalStretch(0)
        self.setSizePolicy(size_policy)
        self.setMinimumSize(QtCore.QSize(INFO_AREA_MIN_WIDTH, 200))

        self.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.setFrameShadow(QtWidgets.QFrame.Raised)
        self.setObjectName("info_area")

        self.layout = QtWidgets.QVBoxLayout(self)

        self.settings_area = SettingsArea(self)
        self.image_info_area = ImageInfoArea(self)
        self.state_area = StateArea(self)

        self.layout.addWidget(self.state_area)
        self.layout.addWidget(self.image_info_area)
        self.layout.addWidget(self.settings_area)

        self.last_image_time = None
        self.image_count = 0

        # Starting a timer to update data every second
        self._updateInfo()
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self._updateInfo)
        self.timer.start(1000)

    def setSettings(self, settings_data):
        return self.settings_area.setSettings(settings_data)

    def showImage(self, image):
        """
        Updates the info area with data about the image being shown.
        """
        data = [("Image Name", image.name),
                ("Height", image.plane_position.dispHeight()),
                ("Pitch", image.plane_orientation.dispPitch()),
                ("Roll", image.plane_orientation.dispRoll()),
                ("Yaw", image.plane_orientation.dispYaw()),
                ("Plane Position", image.plane_position.dispLatLon()),]
        self.image_info_area.updateData(data)

    def addImage(self, image):
        """
        Keeping track of when the last image was added and updating
        info as needed.
        """
        self.last_image_time = datetime.datetime.now()
        self.image_count += 1
        self._updateInfo()

    def _updateInfo(self):
        """
        Update the state information.
        """
        if self.last_image_time:
            timedelta = datetime.datetime.now() - self.last_image_time
            last_image_time_ago = "%s s" % int(timedelta.total_seconds())
        else:
            last_image_time_ago = "(none received)"

        data = [("Image Count", self.image_count),
                ("Time since last image", last_image_time_ago),]
        self.state_area.updateData(data)


class MainImageArea(QtWidgets.QWidget):
    image_clicked = QtCore.pyqtSignal(Image, QtCore.QPoint)
    image_right_clicked = QtCore.pyqtSignal(Image, QtCore.QPoint)

    def __init__(self, *args, settings_data={}, ground_control_points=[], **kwargs):
        super().__init__(*args, **kwargs)
        self.settings_data = settings_data
        self.ground_control_points = ground_control_points

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

        self.image_area = PixmapLabel()
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

        # Ground Control Points as drawn:
        self.ground_control_point_pixmap_label_markers = []

    def showImage(self, image):
        self._clearGroundControlPoints()

        self.image = image
        self.image_area.setPixmap(image.pixmap)

        if self.settings_data.get("Plane Plumbline", True):
            self._drawPlanePlumb()
        elif self.plumbline:
            self.plumbline.hide()

        self._drawGroundControlPoints()

    def _drawPlanePlumb(self):
        """
        Draw a little plane icon on the image at the point directly 
        below the plane.
        """
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

    def _clearGroundControlPoints(self):
        for pixmap_label_marker in self.ground_control_point_pixmap_label_markers:
            pixmap_label_marker.deleteLater()
        self.ground_control_point_pixmap_label_markers = []

    def _drawGroundControlPoints(self):
        """
        Draw a little point on the image for all the ground control points
        that are located in the image.
        """

        for ground_control_point in self.ground_control_points:
            pixel_x, pixel_y = self.image.invGeoReferencePoint(ground_control_point.position)
            if pixel_x and pixel_y:
                point = QtCore.QPoint(pixel_x, pixel_y)
                pixmap_label_marker = PixmapLabelMarker(self, icons.ground_control_point, (10, 10))
                self.image_area.addPixmapLabelFeature(pixmap_label_marker)
                pixmap_label_marker.moveTo(point)
                pixmap_label_marker.show()

                self.ground_control_point_pixmap_label_markers.append(pixmap_label_marker)



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


class MarkerArea(QtWidgets.QFrame):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        size_policy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.MinimumExpanding)
        size_policy.setHorizontalStretch(0)
        size_policy.setVerticalStretch(0)
        self.setSizePolicy(size_policy)
        self.setMinimumSize(QtCore.QSize(MARKER_AREA_MIN_WIDTH, 200))

        self.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.setFrameShadow(QtWidgets.QFrame.Raised)
        self.setObjectName("marker_area")

        self.title = QtWidgets.QLabel(self)
        self.title.setText(translate("MarkerArea", "Marker List"))

        markPoint = QtWidgets.QPushButton("Add", self)
        markPoint.clicked.connect(self.addPoint)
        markPoint.resize(markPoint.minimumSizeHint())
        markPoint.move(0,0)

        markPoint = QtWidgets.QPushButton("Remove", self)
        markPoint.clicked.connect(self.removePoint)
        markPoint.resize(markPoint.minimumSizeHint())
        markPoint.move(120,0)

        markPoint = QtWidgets.QPushButton("Calc Dist", self)
        markPoint.clicked.connect(self.calcDist)
        markPoint.resize(markPoint.minimumSizeHint())
        markPoint.move(0,50)

        markPoint = QtWidgets.QPushButton("Calc Area", self)
        markPoint.clicked.connect(self.calcArea)
        markPoint.resize(markPoint.minimumSizeHint())
        markPoint.move(120,50)

        markPoint = QtWidgets.QPushButton("Export", self)
        markPoint.clicked.connect(self.exportText)
        markPoint.resize(markPoint.minimumSizeHint())
        markPoint.move(0,100)

        markPoint = QtWidgets.QPushButton("Clear", self)
        markPoint.clicked.connect(self.clearMarker)
        markPoint.resize(markPoint.minimumSizeHint())
        markPoint.move(120,100)


    def addPoint(self):
        print("Dummy Function {add Last Point to Marker!}")

    def removePoint(self):
        print("Dummy Function {remove Last Point to Marker!}")

    def calcDist(self):
        print("Dummy Function {refresh Distance calc!}")

    def calcArea(self):
        print("Dummy Function {refresh Area calc!}")

    def exportText(self):
        print("Dummy Function {Export Functionality!}")

    def clearMarker(self):
        print("Dummy Function {Clear Marker!}")


class ThumbnailArea(QtWidgets.QWidget):
    def __init__(self, *args, settings_data={}, **kwargs):
        super().__init__(*args, **kwargs)
        self.settings_data = settings_data

        size_policy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.MinimumExpanding, QtWidgets.QSizePolicy.Preferred)
        size_policy.setHorizontalStretch(10)
        size_policy.setVerticalStretch(10)
        self.setSizePolicy(size_policy)
        self.setMinimumSize(QtCore.QSize(200, THUMBNAIL_AREA_MIN_HEIGHT))

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
            raise(NotImplementedError())

        icon = QtGui.QIcon(image.pixmap)
        item = QtWidgets.QListWidgetItem('', self.contents)
        item.setIcon(icon)
        item.image = image

        if self.settings_data.get("Follow Images", False):
            item.setSelected(True)
            self.contents.scrollToItem(item)

        self.recent_image.setPixmap(image.pixmap)
        self.recent_image.image = image

class BaseListForm(QtWidgets.QWidget):
    """
    Provides a simple list of textual information that can be updated
    programatically.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.setObjectName("state_area")

        title = self._title()
        if title:
            self.title = BoldQLabel(self)
            self.title.setText(translate(self.__class__.__name__, title))
        else:
            self.title = None

        self.layout = QtWidgets.QGridLayout(self)

        self.layout.addWidget(self.title, 0, 0, 1, 2)

        self.fields = None

    def _createFields(self, data):
        """
        Creates the UI elements to display the data.
        """
        self.fields = {}

        for (i, (field_name, field_value)) in enumerate(data):
            label = QtWidgets.QLabel(self)
            label.setText(translate(self.__class__.__name__, field_name))

            value = QtWidgets.QLineEdit(self)
            value.setReadOnly(True)
            value.setText(str(field_value))

            self.layout.addWidget(label, i+1, 0, 1, 1)
            self.layout.addWidget(value, i+1, 1, 1, 1)

            self.fields[field_name] = (label, value)

    def updateData(self, data):
        """
        data should be a list of tuples. The first element of tuple
        will be used as the field name and the second as the field
        value.

        The fiels names should be unique and the same field names
        should be provided each time.
        """
        if not self.fields:
            self._createFields(data)

        if not data:
            return

        for field_name, field_value in data:
            label, value = self.fields[field_name]
            value.setText(str(field_value))

class ImageInfoArea(BaseListForm):
    def _title(self):
        return "Image:"

class StateArea(BaseListForm):
    def _title(self):
        return "State:"

class SettingsArea(QtWidgets.QWidget):
    """
    Provides a simple form for displaying and editing settings.
    The settings should be provided in settings_data, a dictionary of
    strings and bools (only supported types at the moment). The 
    dictionary keys should be strings and as the setting label.
    """

    settings_save_requested = QtCore.pyqtSignal(dict)
    settings_load_requested = QtCore.pyqtSignal()

    def __init__(self, *args, settings_data={}, **kwargs):
        super().__init__(*args, **kwargs)

        # size_policy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.MinimumExpanding, QtWidgets.QSizePolicy.Minimum)
        # size_policy.setHorizontalStretch(0)
        # size_policy.setVerticalStretch(0)
        # self.setSizePolicy(size_policy)
        # self.setMinimumSize(QtCore.QSize(0, 400))

        # self.setFrameShape(QtWidgets.QFrame.StyledPanel)
        # self.setFrameShadow(QtWidgets.QFrame.Raised)
        self.setObjectName("settings_area")

        self.title = BoldQLabel(self)
        self.title.setText(translate("SettingsArea", "Settings:"))

        self.layout = QtWidgets.QGridLayout(self)

        self.settings_layout = QtWidgets.QGridLayout()
        self.buttons_layout = QtWidgets.QGridLayout()

        self.layout.addLayout(self.settings_layout, 0, 0)
        self.layout.addLayout(self.buttons_layout, 1, 0)

        self.settings_layout.addWidget(self.title, 0, 0, 1, 2)

        self.fields = None

    def _createFields(self, settings_data):
        """
        Creates the UI elements to display the settings.
        """
        self.fields = {}

        if not settings_data:
            return

        # Creating the widgets
        for (i, (field_name, field_value)) in enumerate(settings_data.items()):
            setting_label = QtWidgets.QLabel(self)
            setting_label.setText(translate("SettingsArea", field_name))

            if isinstance(field_value, bool):
                edit_widget = QtWidgets.QCheckBox(self)
                edit_widget.setChecked(field_value)
            elif isinstance(field_value, str):
                edit_widget = QtWidgets.QLineEdit(self)
                edit_widget.setText(field_value)
            else:
                raise(ValueError("Only string and boolean settings supported. %s provided for field '%s'." % (type(field_value).__name__, field_name)))

            self.settings_layout.addWidget(setting_label, i+1, 0, 1, 1)
            self.settings_layout.addWidget(edit_widget, i+1, 1, 1, 1)

            self.fields[field_name] = (setting_label, edit_widget)

        self.load_button = QtWidgets.QPushButton(translate("SettingsArea", "Load"), self)
        self.buttons_layout.addWidget(self.load_button, i+1, 0, 1, 1)
        self.save_button = QtWidgets.QPushButton(translate("SettingsArea", "Save"), self)
        self.buttons_layout.addWidget(self.save_button, i+1, 1, 1, 1)

        self.load_button.clicked.connect(self.settings_load_requested)
        self.save_button.clicked.connect(lambda: self.settings_save_requested.emit(self.getSettings()))


    def setSettings(self, settings_data):
        """
        Update the displayed settings to match the values in settings_data.
        This dict must have the same keys each time this method is called.
        """
        if not self.fields:
            self._createFields(settings_data)

        if not settings_data:
            return

        for field_name, field_value in settings_data.items():
            setting_label, edit_widget = self.fields[field_name]

            if isinstance(field_value, bool):
                edit_widget.setChecked(field_value)
            elif isinstance(field_value, str):
                edit_widget.setText(field_value)
            else:
                raise(ValueError())

    def getSettings(self):
        """
        Return a dictionary of the settings, potentially updated by the user.
        """
        if not self.fields:
            return None
        output = {}
        for (field_name, (setting_label, edit_widget)) in self.fields.items():
            if isinstance(edit_widget, QtWidgets.QCheckBox):
                field_value = bool(edit_widget.checkState())
            elif isinstance(edit_widget, QtWidgets.QLineEdit):
                field_value = edit_widget.text()
            else:
                raise(ValueError())

            output[field_name] = field_value

        return output