import sys
import logging
import signal # For exiting pigeon from terminal

from PyQt5 import Qt, QtCore, QtGui, QtWidgets
translate = QtCore.QCoreApplication.translate

from features import BaseFeature, Feature, Marker
from geo import position_at_offset

from .common import QueueMixin
from .commonwidgets import NonEditableBaseListForm
from .pixmaploader import PixmapLoader
from .style import stylesheet
from ui import icons

from .areas import InfoArea
from .areas import ThumbnailArea
from .areas import FeatureArea
from .areas import MainImageArea
from .areas import SettingsArea

THUMBNAIL_AREA_START_HEIGHT = 100
THUMBNAIL_AREA_MIN_HEIGHT = 60
INFO_AREA_MIN_WIDTH = 250
FEATURE_AREA_MIN_WIDTH = 300

def noop():
    pass

class UI(QtCore.QObject, QueueMixin):
    """
    Class for the rest of the application to interface with the UI.

    This implementation of the class uses PyQt5 to provide the UI but
    theoretically, other frameworks could be used without the rest of
    the application caring, as long as this class's API is
    implemented. Or, more likely: a mock UI instance could be used in
    unit testing for easy testing of the rest of the application.
    """
    settings_changed = QtCore.pyqtSignal(dict)

    def __init__(self, save_settings, load_settings, export_manager, image_in_queue, feature_io_queue, uav, ground_control_points=[], about_text=""):
        super().__init__()
        self.logger = logging.getLogger(__name__ + "." + self.__class__.__name__)
        self.settings_data = load_settings()
        self.features = ground_control_points # For all features, not just GCP's
        self.feature_io_queue = feature_io_queue
        self.uav = uav
        self.save_settings = save_settings

        self.app = QtWidgets.QApplication(sys.argv)
        self.app.setStyleSheet(stylesheet)
        self.main_window = MainWindow(self.settings_data, self.features, export_manager, about_text, self.app.exit)

        self.main_window.settings_save_requested.connect(self.settings_changed.emit)

        self.main_window.feature_area.feature_detail_area.addSubfeatureRequested.connect(self.main_window.collectSubfeature)

        self.uav.addCommandAckedCb(self.main_window.info_area.controls_area.receive_command_ack.emit)
        self.main_window.info_area.controls_area.send_command.connect(self.uav.sendCommand)

        self.uav.addUAVConnectedChangedCb(self.main_window.info_area.controls_area.uav_connection_changed.emit)
        self.uav.addUAVStatusCb(self.main_window.info_area.controls_area.receive_status_message.emit)

        self.connectQueue(self.feature_io_queue.in_queue, self.applyFeatureSync)

        self.connectQueue(image_in_queue, self.addImage)
        signal.signal(signal.SIGINT, lambda signum, fram: self.app.exit())

        # Hooking up some inter-component behaviour
        self.main_window.featureChangedLocally.connect(lambda feature: self.feature_io_queue.out_queue.put(feature))
        self.main_window.featureAddedLocally.connect(lambda feature: self.feature_io_queue.out_queue.put(feature))

        self.settings_changed.connect(self.save_settings)
        self.settings_changed.connect(lambda changed_data: self.main_window.main_image_area._drawPlanePlumb())
        self.settings_changed.connect(lambda changed_data: self.main_window.info_area.settings_area.setSettings(self.settings_data))
        def update_settings_window_settings():
            if self.main_window.settings_window:
                self.main_window.settings_window.settings_area.setSettings(self.settings_data)
        self.settings_changed.connect(update_settings_window_settings)


    def run(self):
        self.main_window.show()
        self.startQueueMonitoring()
        return self.app.exec_()

    def addImage(self, image):
        self.main_window.addImage(image)

    def applyFeatureSync(self, feature):
        for i, existing_feature in enumerate(self.features):
            if existing_feature.id == feature.id:
                self.features[i] = feature
                self.main_window.featureChanged.emit(feature)
                break
            else:
                if existing_feature.updateSubfeature(feature):
                    self.main_window.featureChanged.emit(feature)
                    break
        else:
            self.main_window.featureAdded.emit(feature)


class AboutWindow(QtWidgets.QWidget):
    def __init__(self, *args, about_text="", **kwargs):
        super().__init__(*args, **kwargs)
        self.setObjectName("about_window")
        self.setFixedSize(QtCore.QSize(550, 250))
        self.setWindowTitle(translate("About Window", "About"))

        frame_rect = self.frameGeometry()
        center_point = QtWidgets.QApplication.desktop().availableGeometry().center()
        frame_rect.moveCenter(center_point)
        self.move(frame_rect.topLeft())

        self.layout = QtWidgets.QVBoxLayout(self)
        about_label = QtWidgets.QLabel(about_text, self)
        about_label.setAlignment(Qt.Qt.AlignCenter)
        self.layout.addWidget(about_label)

class SettingsWindow(QtWidgets.QWidget):
    settings_save_requested = QtCore.pyqtSignal(dict)

    def __init__(self, *args, settings_data={}, **kwargs):
        super().__init__(*args, **kwargs)
        self.setObjectName("settings_window")
        self.setMinimumSize(QtCore.QSize(400, 300))
        size_policy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        size_policy.setHorizontalStretch(1)
        size_policy.setVerticalStretch(1)
        self.setSizePolicy(size_policy)
        self.setWindowTitle(translate("Settings Window", "Settings"))

        frame_rect = self.frameGeometry()
        center_point = QtWidgets.QApplication.desktop().availableGeometry().center()
        frame_rect.moveCenter(center_point)
        self.move(frame_rect.topLeft())

        self.layout = QtWidgets.QVBoxLayout(self)
        self.settings_area = SettingsArea(self, settings_data=settings_data, fields_to_display=sorted(settings_data.keys()))
        self.layout.addWidget(self.settings_area)
        self.layout.setAlignment(self.settings_area, Qt.Qt.AlignCenter)

        self.settings_area.settings_save_requested.connect(self.settings_save_requested.emit)

class MainWindow(QtWidgets.QMainWindow):
    featureChanged = QtCore.pyqtSignal(BaseFeature) # For anytime a feature is changed (including by other Pigeon istances: they would trigger this signal).
    featureChangedLocally = QtCore.pyqtSignal(BaseFeature) # For anytime this Pigeon instance triggers feature change: will result in syncing to other Pigeons.
    featureAdded = QtCore.pyqtSignal(BaseFeature) # Same as featureChanged but for new features.
    featureAddedLocally = QtCore.pyqtSignal(BaseFeature) # Same as featureChangedLocally but for new featuers.

    settings_save_requested = QtCore.pyqtSignal(dict)

    def __init__(self, settings_data={}, features=[], export_manager=None, about_text="", exit_cb=noop):
        super().__init__()
        self.settings_data = settings_data
        self.features = features
        self.export_manager = export_manager
        self.about_text = about_text
        self.exit_cb = exit_cb

        self.about_window = None
        self.settings_window = None

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

        # Hooking up some inter-component behaviour.
        self.thumbnail_area.contents.currentItemChanged.connect(lambda new_item, old_item: self.showImage(new_item.image)) # Show the image that's selected
        self.main_image_area.image_clicked.connect(self.handleMainImageClick)

        self.info_area.settings_area.settings_save_requested.connect(self.settings_save_requested.emit)
        #self.main_image_area.ruler.ruler_updated.connect(self.info_area.ruler_updated)

        # Hooking up feature inter-component behaviour. Listing all things we could do to change a feature and hooking them up internally and externally
        for slot in [self.feature_area.feature_detail_area.featureChanged, # Feature's details can be changed
                     self.main_image_area.featureChanged,                  # Feature's position can be changed when it's dragged
                    ]:
            slot.connect(self.featureChanged.emit)        # To let other components within this Pigeon know.
            slot.connect(self.featureChangedLocally.emit) # To let other Pigeon's know.

        # These are the components that need to know when a feature is changed:
        self.featureChanged.connect(self.feature_area.updateFeature)                     # Update the feature in the list
        self.featureChanged.connect(self.main_image_area.updateFeature)                  # Update the feature in the main image window
        self.featureChanged.connect(self.feature_area.feature_detail_area.updateFeature) # Update the feature details

        # And things that need to know when a new feature is added, whether initiated by this Pigeon or another instance:
        for signal in [self.featureAdded, self.featureAddedLocally]:
            signal.connect(lambda feature: self.features.append(feature))
            signal.connect(self.main_image_area.addFeature)
            signal.connect(self.feature_area.addFeature)

        self.initMenuBar()
        QtCore.QMetaObject.connectSlotsByName(self)

    def initMenuBar(self):
        self.menubar = self.menuBar()

        menu = self.menubar.addMenu("&File")

        exit_action = QtWidgets.QAction("Exit", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.exit_cb)

        menu.addAction(exit_action)

        if self.export_manager:
            menu = self.menubar.addMenu("&Export")
            for option_name, option_action, shortcut in self.export_manager.options:
                action_widget = QtWidgets.QAction(option_name, self)
                def closure(action):
                    return lambda enabled: action(self.features)
                action_widget.triggered.connect(closure(option_action))
                if shortcut:
                    action_widget.setShortcut(shortcut)
                menu.addAction(action_widget)

        menu = self.menubar.addMenu("&Edit")
        settings_action = QtWidgets.QAction("Settings", self)
        settings_action.triggered.connect(self.showSettingsWindow)
        menu.addAction(settings_action)

        menu = self.menubar.addMenu("&Help")

        about_action = QtWidgets.QAction("About Pigeon", self)
        about_action.setShortcut("Ctrl+A")
        about_action.triggered.connect(self.showAboutWindow)

        menu.addAction(about_action)

    def showAboutWindow(self):
        self.about_window = AboutWindow(about_text=self.about_text)
        self.about_window.show()

    def showSettingsWindow(self):
        self.settings_window = SettingsWindow(settings_data=self.settings_data)
        self.settings_window.show()
        self.settings_window.settings_save_requested.connect(self.settings_save_requested.emit)

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

    def createNewMarker(self, image, point):
        marker = Marker(image, point=(point.x(), point.y()))
        if marker.position:
            offset_position = position_at_offset(marker.position, float(self.settings_data["Nominal Target Size"]), 0)
            offset_pixel_x, offset_pixel_y = image.invGeoReferencePoint(offset_position)

            if offset_pixel_x and offset_pixel_y:
                offset_pixels = max(abs(offset_pixel_x - point.x()), abs(offset_pixel_y - point.y()))

                # Calculate thumbnail size and crop
                cropping_rect = QtCore.QRect(point.x() - offset_pixels, point.y() - offset_pixels, offset_pixels * 2, offset_pixels * 2)
                marker.picture = image.pixmap_loader.getPixmapForSize(None).copy(cropping_rect)

            self.featureAddedLocally.emit(marker)

    def collectSubfeature(self, feature):
        self.collect_subfeature_for = feature

    def handleMainImageClick(self, image, point):
        if self.collect_subfeature_for:
            self.collect_subfeature_for.updatePoint(image, (point.x(), point.y()))
            self.featureChanged.emit(self.collect_subfeature_for)
            self.collect_subfeature_for = None
        else:
            self.createNewMarker(image, point)

    def closeEvent(self, event):
        self.exit_cb() # Terminating the whole program if the main window is closed
