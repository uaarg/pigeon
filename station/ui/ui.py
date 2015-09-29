import sys
import logging
import datetime

from PyQt5 import QtCore, QtGui, QtWidgets
translate = QtCore.QCoreApplication.translate

from image import Image
from features import Marker, Feature

from .common import PixmapLabel, WidthForHeightPixmapLabel, PixmapLabelMarker, BoldQLabel, BaseQListWidget, ListImageItem, ScaledListWidget, QueueMixin
from .commonwidgets import EditableBaseListForm
from .pixmaploader import PixmapLoader
from .style import stylesheet
from ui import icons

THUMBNAIL_AREA_START_HEIGHT = 100
THUMBNAIL_AREA_MIN_HEIGHT = 60
INFO_AREA_MIN_WIDTH = 250
FEATURE_AREA_MIN_WIDTH = 250

class UI(QtCore.QObject, QueueMixin):
    """
    Class for the rest of the application to interface with the UI.

    This implementation of the class uses PyQt5 to provide the UI but
    theoretically, other frameworks could be used without the rest of
    the application caring, as long as this class's API is
    implemented. Or, more likely: a mock UI instance could be used in
    unit testing for easy testing of the rest of the application.
    """
    settings_changed = QtCore.pyqtSignal()

    def __init__(self, save_settings, load_settings, image_queue, ground_control_points=[]):
        super().__init__()
        self.logger = logging.getLogger(__name__ + "." + self.__class__.__name__)
        self.settings_data = load_settings()
        self.features = ground_control_points # For all features, not just GCP's

        self.app = QtWidgets.QApplication(sys.argv)
        self.app.setStyleSheet(stylesheet)
        self.main_window = MainWindow(self.settings_data, self.features)

        self.main_window.info_area.settings_area.settings_load_requested.connect(lambda: self.main_window.info_area.settings_area.setSettings(load_settings()))
        self.main_window.info_area.settings_area.settings_load_requested.connect(lambda: self.settings_changed.emit())
        self.main_window.info_area.settings_area.settings_save_requested.connect(save_settings)
        self.main_window.info_area.settings_area.settings_save_requested.connect(lambda: self.settings_changed.emit())

        self.connectQueue(image_queue, self.addImage)

        def print_image_clicked(image, point):
            string = "Point right clicked in image %s: %s" % (image.name, image.geoReferencePoint(point.x(), point.y()))
            print(string)
            self.logger.info(string)

        def create_new_marker(image, point):
            position = image.geoReferencePoint(point.x(), point.y())
            marker = Marker(position)

            cropping_rect = QtCore.QRect(point.x() - 40, point.x() + 40, point.y() - 40, point.y() + 40)
            marker.picture = image.pixmap_loader.getPixmapForSize(None).copy(cropping_rect)
            self.addFeature(image, marker)

        # Hooking up some inter-component behaviour
        self.main_window.main_image_area.image_clicked.connect(create_new_marker)
        self.main_window.main_image_area.image_right_clicked.connect(print_image_clicked)
        self.settings_changed.connect(lambda: self.main_window.main_image_area._drawPlanePlumb())

    def run(self):
        self.main_window.info_area.settings_area.settings_load_requested.emit()
        self.main_window.show()
        self.startQueueMonitoring()
        return self.app.exec_()

    def addImage(self, image):
        self.main_window.addImage(image)

    def addFeature(self, image, feature):
        feature.image = image
        self.features.append(feature)
        self.main_window.addFeature(feature)



class MainWindow(QtWidgets.QMainWindow):
    def __init__(self, settings_data={}, features=[]):
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
        self.main_image_area = MainImageArea(self.main_horizontal_split, settings_data=settings_data, features=features)
        self.feature_area = FeatureArea(self.main_horizontal_split)
        self.thumbnail_area = ThumbnailArea(self.main_vertical_split, settings_data=settings_data)

        # Hooking up some inter-component benhaviour
        self.thumbnail_area.contents.currentItemChanged.connect(lambda new_item, old_item: self.showImage(new_item.image)) # Show the image that's selected
        self.feature_area.feature_list.currentItemChanged.connect(lambda new_item, old_item: self.feature_area.showFeature(new_item.feature)) # Show feature details for the selected feature
        self.feature_area.feature_detail_area.featureChanged.connect(self.feature_area.updateFeature) # Update the feature in the list when it's details are changed
        self.feature_area.feature_detail_area.featureChanged.connect(self.main_image_area._drawFeature) # Re-draw the feature when its details are changed (including re-setting its tooltip)


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
        image.pixmap_loader = PixmapLoader(image.path)

        # Recording the width and height of the image for other code to use:
        image.width = image.pixmap_loader.width()
        image.height = image.pixmap_loader.height()

        if self.settings_data.get("Follow Images", False) or not self.current_image:
            self.showImage(image)
        self.thumbnail_area.addImage(image)
        self.info_area.addImage(image)
        image.pixmap_loader.optimizeMemory()

    def setSettings(self, settings_data):
        return self.info_area.setSettings(settings_data)

    def showImage(self, image):
        if self.current_image:
            self.current_image.pixmap_loader.freeOriginal()
            self.current_image.pixmap_loader.optimizeMemory()
        self.current_image = image
        self.current_image.pixmap_loader.holdOriginal()
        self.main_image_area.showImage(image)
        self.info_area.showImage(image)

    def addFeature(self, feature):
        self.feature_area.addFeature(feature)
        self.main_image_area.addFeature(feature)

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
        self.image_info_area = ImageInfoArea(self, editable=False)
        self.state_area = StateArea(self, editable=False)

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
        return self.settings_area.setData(settings_data)

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
        self.image_info_area.setData(data)

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

        data = [("Image Count", str(self.image_count)),
                ("Time since last image", str(last_image_time_ago)),]
        self.state_area.setData(data)


class MainImageArea(QtWidgets.QWidget):
    image_clicked = QtCore.pyqtSignal(Image, QtCore.QPoint)
    image_right_clicked = QtCore.pyqtSignal(Image, QtCore.QPoint)

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

        # Features as drawn:
        self.feature_pixmap_label_markers = []

    def showImage(self, image):
        self._clearFeatures()

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

    def _clearFeatures(self):
        for pixmap_label_marker in self.feature_pixmap_label_markers:
            pixmap_label_marker.deleteLater()
        self.feature_pixmap_label_markers = []

    def _drawFeature(self, feature):
        pixel_x, pixel_y = self.image.invGeoReferencePoint(feature.position)
        if pixel_x and pixel_y:
            point = QtCore.QPoint(pixel_x, pixel_y)
            pixmap_label_marker = PixmapLabelMarker(self, icons.name_map[feature.icon_name], feature.icon_size)
            self.image_area.addPixmapLabelFeature(pixmap_label_marker)
            pixmap_label_marker.moveTo(point)
            pixmap_label_marker.setToolTip(str(feature))
            pixmap_label_marker.show()

            self.feature_pixmap_label_markers.append(pixmap_label_marker)

    def _drawFeatures(self):
        for feature in self.features:
            self._drawFeature(feature)

    def addFeature(self, feature):
        self._drawFeature(feature)

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


class FeatureDetailArea(EditableBaseListForm):
    featureChanged = QtCore.pyqtSignal(Feature)
    def __init__(self):
        super().__init__()
        self.feature = None
        self.dataEdited.connect(lambda data: self._editFeatureData(data))

    def _title(self):
        return "Feature Detail:"

    def _editFeatureData(self, data):
        for i, (field_name, field_value) in enumerate(self.feature.data):
            for data_name, data_value in data:
                if field_name == data_name:
                    self.feature.data[i] = (field_name, data_value)
                    break
        self.featureChanged.emit(self.feature)

    def showFeature(self, feature):
        self.feature = feature
        data = feature.data.copy()
        data.append(("Position", feature.position.dispLatLon(), False))
        data.append(("Image Name", str(feature.image.name), False))
        self.setData(data)


class FeatureArea(QtWidgets.QFrame):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        size_policy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.MinimumExpanding)
        size_policy.setHorizontalStretch(0)
        size_policy.setVerticalStretch(0)
        self.setSizePolicy(size_policy)
        self.setMinimumSize(QtCore.QSize(FEATURE_AREA_MIN_WIDTH, 200))

        self.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.setFrameShadow(QtWidgets.QFrame.Raised)
        self.setObjectName("feature_area")

        self.title = BoldQLabel(self)
        self.title.setText(translate("FeatureArea", "Marker List:"))

        self.layout = QtWidgets.QGridLayout(self)

        self.layout.addWidget(self.title, 0, 0, 1, 1)

        self.feature_list = BaseQListWidget(self)
        self.feature_list.setFrameShape(QtWidgets.QFrame.NoFrame)
        self.feature_list.setFlow(QtWidgets.QListWidget.TopToBottom)
        self.layout.addWidget(self.feature_list, 1, 0, 1, 1)

        self.feature_detail_area = FeatureDetailArea()
        self.layout.addWidget(self.feature_detail_area, 2, 0, 1, 1)

    def addFeature(self, feature):
        item = QtWidgets.QListWidgetItem("", self.feature_list)
        item.setText(str(feature))
        item.feature = feature
        feature.feature_area_item = item
        if feature.picture:
            icon = QtGui.QIcon(feature.picture)
            item.setIcon(icon)
        self.showFeature(feature)

    def showFeature(self, feature):
        self.feature_detail_area.showFeature(feature)
        self.feature_list.setCurrentItem(feature.feature_area_item)

    def updateFeature(self, feature):
        for item in self.feature_list.iterItems():
            if item.feature == feature:
                item.setText(str(feature))
                break

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
        self.logger = logging.getLogger(__name__ + "." + self.__class__.__name__)
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

        item = ListImageItem(image.pixmap_loader, self.contents)
        item.image = image

        if self.settings_data.get("Follow Images", False):
            item.setSelected(True)
            self.contents.scrollToItem(item)

        self.logger.debug("Setting recent image pixmap")
        self.recent_image.setPixmap(image.pixmap_loader)
        self.recent_image.image = image

class ImageInfoArea(EditableBaseListForm):
    def _title(self):
        return "Image:"

class StateArea(EditableBaseListForm):
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


    def __init__(self, *args, **kwargs):
        super(QtWidgets.QWidget, self).__init__(*args, **kwargs)

        self.layout = QtWidgets.QVBoxLayout()

        self.title = BoldQLabel(self)
        self.title.setText(translate("SettingsArea", "Settings:"))
        self.layout.addWidget(self.title)

        self.edit_form = EditableBaseListForm(self)
        self.layout.addWidget(self.edit_form)

        self.setLayout(self.layout)

        self.buttons_layout = QtWidgets.QHBoxLayout()
        self.layout.addLayout(self.buttons_layout)

        self.load_button = QtWidgets.QPushButton(translate("SettingsArea", "Load"), self)
        self.save_button = QtWidgets.QPushButton(translate("SettingsArea", "Save"), self)
        self.buttons_layout.addWidget(self.load_button)
        self.buttons_layout.addWidget(self.save_button)

        self.load_button.clicked.connect(self.settings_load_requested)
        self.save_button.clicked.connect(lambda: self.settings_save_requested.emit(self.getSettings()))


    def setSettings(self, settings_data):
        data = [(field_name, field_value) for field_name, field_value in settings_data.items()]
            # Converting the dictinary to a list of tuples because this is what the EditableBaseListForm needs
        self.edit_form.setData(data)

    def getSettings(self):
        data = self.edit_form.getData()
        settings_data = {row[0]:row[1] for row in data}
        return settings_data
