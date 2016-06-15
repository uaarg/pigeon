import sys
import logging
import signal # For exiting pigeon from terminal

from PyQt5 import QtCore, QtGui, QtWidgets
translate = QtCore.QCoreApplication.translate

from features import BaseFeature, Feature, Marker

from .common import QueueMixin
from .pixmaploader import PixmapLoader
from .style import stylesheet
from ui import icons

from .areas import InfoArea
from .areas import ThumbnailArea
from .areas import FeatureArea
from .areas import MainImageArea

from geo import position_at_offset

THUMBNAIL_AREA_START_HEIGHT = 100
THUMBNAIL_AREA_MIN_HEIGHT = 60
INFO_AREA_MIN_WIDTH = 250
FEATURE_AREA_MIN_WIDTH = 300

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

    def ExitFcn (self, signum, fram):
        # Exiting Program from the Terminal
        self.app.exit()

    def __init__(self, save_settings, load_settings, export_manager, image_queue, uav, ground_control_points=[]):
        super().__init__()
        self.logger = logging.getLogger(__name__ + "." + self.__class__.__name__)
        self.settings_data = load_settings()
        self.features = ground_control_points # For all features, not just GCP's
        self.uav = uav

        self.app = QtWidgets.QApplication(sys.argv)
        self.app.setStyleSheet(stylesheet)
        self.main_window = MainWindow(self.settings_data, self.features, export_manager, self.app.exit)

        self.main_window.info_area.settings_area.settings_load_requested.connect(lambda: self.main_window.info_area.settings_area.setSettings(load_settings()))
        self.main_window.info_area.settings_area.settings_load_requested.connect(self.settings_changed.emit)
        self.main_window.info_area.settings_area.settings_save_requested.connect(save_settings)
        self.main_window.info_area.settings_area.settings_save_requested.connect(self.settings_changed.emit)

        self.main_window.feature_area.feature_detail_area.addSubfeatureRequested.connect(self.main_window.collectSubfeature)

        self.uav.addCommandAckedCb(self.main_window.info_area.controls_area.receive_command_ack.emit)
        self.main_window.info_area.controls_area.send_command.connect(self.uav.sendCommand)

        self.uav.addUAVConnectedChangedCb(self.main_window.info_area.controls_area.uav_connection_changed.emit)
        self.uav.addUAVStatusCb(self.main_window.info_area.controls_area.receive_status_message.emit)

        self.connectQueue(image_queue, self.addImage)
        signal.signal(signal.SIGINT,self.ExitFcn)

        # Hooking up some inter-component behaviour
        self.main_window.main_image_area.image_right_clicked.connect(self.main_window.main_image_area.updateRuler)
        self.settings_changed.connect(lambda: self.main_window.main_image_area._drawPlanePlumb())

    def run(self):
        self.main_window.info_area.settings_area.settings_load_requested.emit()
        self.main_window.show()
        self.startQueueMonitoring()
        return self.app.exec_()

    def addImage(self, image):
        self.main_window.addImage(image)

class MainWindow(QtWidgets.QMainWindow):
    featureChanged = QtCore.pyqtSignal(BaseFeature)

    def __init__(self, settings_data={}, features=[], export_manager=None, exitfcnCB= None):
        super().__init__()
        self.settings_data = settings_data
        self.features = features
        self.export_manager = export_manager
        self.ExitingCB = exitfcnCB

        # State
        self.collect_subfeature_for = None
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
        self.info_area = InfoArea(self.main_horizontal_split, settings_data=settings_data, minimum_width=INFO_AREA_MIN_WIDTH)
        self.main_image_area = MainImageArea(self.main_horizontal_split, settings_data=settings_data, features=features)
        self.feature_area = FeatureArea(self.main_horizontal_split, settings_data=settings_data, minimum_width=FEATURE_AREA_MIN_WIDTH)
        self.thumbnail_area = ThumbnailArea(self.main_vertical_split, settings_data=settings_data, minimum_height=THUMBNAIL_AREA_MIN_HEIGHT)

        # Hooking up some inter-component benhaviour
        self.thumbnail_area.contents.currentItemChanged.connect(lambda new_item, old_item: self.showImage(new_item.image)) # Show the image that's selected
        # self.feature_area.selectedFeatureChanged.connect(lambda new_item, old_item: print("selectedFeatureChanged TODO: implement"))
        self.main_image_area.image_clicked.connect(self.handleMainImageClick)

        self.feature_area.feature_detail_area.featureChanged.connect(self.featureChanged.emit) # Feature's details can be changed
        self.main_image_area.featureChanged.connect(self.featureChanged.emit)  # Feature's position can be changed when it's dragged

        self.featureChanged.connect(self.feature_area.updateFeature) # Update the feature in the list
        self.featureChanged.connect(self.main_image_area.updateFeature) # Update the feature in the main image window
        self.featureChanged.connect(self.feature_area.feature_detail_area.updateFeature) # Update the feature details

        self.initMenuBar()
        QtCore.QMetaObject.connectSlotsByName(self)

    def initMenuBar(self):
        self.menubar = self.menuBar()

        exit_action = QtWidgets.QAction("Exit Pigeon :(", self)
        exit_action.setShortcut('Ctrl+Q')
        exit_action.triggered.connect(self.ExitFcn)

        about_action = QtWidgets.QAction("About Pigeon", self)
        about_action.setShortcut('Ctrl+A')
        about_action.triggered.connect(self.AboutPopup)

        menu = self.menubar.addMenu('&File')
        menu.addAction(about_action)
        menu.addAction(exit_action)

        if self.export_manager:
            menu = self.menubar.addMenu('&Export')
            for option_name, option_action, shortcut in self.export_manager.options:
                action_widget = QtWidgets.QAction(option_name, self)
                def closure(action):
                    return lambda enabled: action(self.features)
                action_widget.triggered.connect(closure(option_action))
                if shortcut:
                    action_widget.setShortcut(shortcut)
                menu.addAction(action_widget)

    def ExitFcn(self):
        print("You pressed Ctrl+Q, now exiting")
        self.ExitingCB()

    def AboutPopup(self):
        print("You pressed Ctrl+S, popup is not working yet")

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
        self.features.append(feature)
        self.main_image_area.addFeature(feature)
        self.feature_area.addFeature(feature)

    def createNewMarker(self, image, point):
        marker = Marker(image, point=(point.x(), point.y()))

        offset_position = position_at_offset(marker.position, float(self.settings_data["Nominal Target Size"]), 0)
        offset_pixel_x, offset_pixel_y = image.invGeoReferencePoint(offset_position)
        offset_pixels = max(abs(offset_pixel_x - point.x()), abs(offset_pixel_y - point.y()))

        # Calculate thumbnail size and crop
        cropping_rect = QtCore.QRect(point.x() - offset_pixels, point.y() - offset_pixels, offset_pixels * 2, offset_pixels * 2)
        marker.picture = image.pixmap_loader.getPixmapForSize(None).copy(cropping_rect)

        self.addFeature(marker)

    def collectSubfeature(self, feature):
        self.collect_subfeature_for = feature

    def handleMainImageClick(self, image, point):
        if self.collect_subfeature_for:
            self.collect_subfeature_for.updatePoint(image, (point.x(), point.y()))
            self.featureChanged.emit(self.collect_subfeature_for)
            self.collect_subfeature_for = None
        else:
            self.createNewMarker(image, point)
