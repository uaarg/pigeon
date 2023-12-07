import sys
import logging
import signal as signal_  # For exiting pigeon from terminal
from queue import Queue

from PyQt6 import QtCore, QtWidgets, QtGui

translate = QtCore.QCoreApplication.translate  # Potential aliasing

from pigeon.features import BaseFeature, Marker, Point

from pigeon.ui.areas import InfoArea, ThumbnailArea, FeatureArea, MainImageArea, SettingsArea
from pigeon.ui.common import QueueMixin
from pigeon.ui.dialogues import QrDiag
from pigeon.ui.pixmaploader import PixmapLoader
from pigeon.ui.style import stylesheet

from pigeon.image import Image
from pigeon.comms.services.messageservice import MavlinkMessage

THUMBNAIL_AREA_START_HEIGHT = 100
THUMBNAIL_AREA_MIN_HEIGHT = 60
INFO_AREA_MIN_WIDTH = 250
FEATURE_AREA_MIN_WIDTH = 300


def noop():
    pass


class UI(QtCore.QObject, QueueMixin):
    """
    Class for the rest of the application to interface with the UI.

    This implementation of the class uses PyQt6 to provide the UI but
    theoretically, other frameworks could be used without the rest of
    the application caring, as long as this class's API is
    implemented. Or, more likely: a mock UI instance could be used in
    unit testing for easy testing of the rest of the application.
    """
    settings_changed = QtCore.pyqtSignal(dict)

    def __init__(self,
                 uav,
                 save_settings,
                 load_settings,
                 image_in_queue,
                 message_in_queue,
                 feature_io_queue,
                 ground_control_points=[],
                 about_text=""):
        super().__init__()

        # Init
        # ====
        self.logger = logging.getLogger(__name__ + "." +
                                        self.__class__.__name__)
        self.settings_data = load_settings()
        self.features = ground_control_points  # For all features, not just GCP's ???
        self.feature_io_queue = feature_io_queue
        self.uav = uav
        self.save_settings = save_settings

        self.app = QtWidgets.QApplication(sys.argv)
        self.app.setStyleSheet(stylesheet)
        self.main_window = MainWindow(self.uav, self.settings_data,
                                      self.features, about_text, self.app.exit)

        self.main_window.settings_save_requested.connect(
            self.settings_changed.emit)

        self.main_window.feature_area.feature_detail_area.addSubfeatureRequested.connect(
            self.main_window.collectSubfeature)

        self.connectSignals(image_in_queue, message_in_queue)

        # Hooking up some inter-component behaviour
        self.main_window.featureChangedLocally.connect(
            lambda feature: self.feature_io_queue.out_queue.put(feature))
        self.main_window.featureAddedLocally.connect(
            lambda feature: self.feature_io_queue.out_queue.put(feature))

        self.settings_changed.connect(self.save_settings)
        self.settings_changed.connect(
            lambda changed_data: self.main_window.info_area.settings_area.
            setSettings(self.settings_data))

        def update_settings_window_settings():
            if self.main_window.settings_window:
                self.main_window.settings_window.settings_area.setSettings(
                    self.settings_data)

        self.settings_changed.connect(update_settings_window_settings)

    def run(self):
        """
        Opens window and starts event loop.

        Returns:
            The exit value after loop ends (int).
        """
        self.main_window.show()
        self.startQueueMonitoring()
        return self.app.exec()

    def addImage(self, image):
        """
        Updates image shown through UI.
        Callback for the image_in_queue signal.

        Parameters:
            image (Image): instance of the Image class
        """
        self.main_window.addImage(image)

    def applyFeatureSync(self, feature):
        """
        Updates features with a new feature. Checks if feature already exists,
        if so then updates, otherwise adds feature.

        Parameters:
            feature (*see BaseFeature.deserialize): feature to check against features already contained in this instance
        """
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

    def connectSignals(self, image_in_queue: Queue, message_in_queue: Queue):
        """
        Hook up various PyQt Signals and emissions to UI elements

        Parameters:
            image_in_queue: holds incoming images to be linked up
            message_in_queue: holds received mavlink messages
        """

        # Callbacks when UAV acknowledges commands
        self.uav.addCommandAckedCb(
            self.main_window.info_area.controls_area.receive_command_ack.emit)
        self.uav.addCommandAckedCb(
            self.main_window.info_area.controls.receive_command_ack.emit)

        # UAV commands sender
        self.main_window.info_area.controls_area.send_command.connect(
            self.uav.sendCommand)
        self.main_window.info_area.controls.send_command.connect(
            self.uav.sendCommand)

        # Various UAV connections
        self.uav.addUAVConnectedChangedCb(
            self.main_window.info_area.controls_area.uav_connection_changed.
            emit)

        self.uav.addLastMessageReceivedCb(
            self.main_window.info_area.controls_area.message_received.emit)

        self.uav.addUAVStatusCb(self.main_window.info_area.controls_area.
                                receive_status_message.emit)

        # Multi-pigeon signals
        self.connectQueue(self.feature_io_queue.in_queue,
                          self.applyFeatureSync)
        self.connectQueue(image_in_queue, self.addImage)
        self.connectQueue(
            message_in_queue,
            self.main_window.mavlinkdebugger_window.handleMessage)

        # Kill signal
        signal_.signal(signal_.SIGINT, lambda signum, fram: self.app.exit())


# ============================================
#                   Windows
# =============================================


class MavLinkDebugger(QtWidgets.QWidget):
    """
    Window that displays all mavlink messages received and sent
    """

    receive_message = QtCore.pyqtSignal(MavlinkMessage)

    def __init__(self) -> None:
        super().__init__()

        self.message_display = QtWidgets.QTextEdit(self)
        self.message_display.setReadOnly(True)

        layout = QtWidgets.QVBoxLayout(self)
        layout.addWidget(self.message_display)

        self.receive_message.connect(self.handleMessage)

    def handleMessage(self, message: MavlinkMessage):
        current_time = message.time.strftime("%H:%M:%S")
        self.message_display.append(
            f"Message: {message.type}, Received: {current_time}")


class AboutWindow(QtWidgets.QWidget):
    """
    Window that brings up information regarding the Pigeon software
    """

    def __init__(self, *args, about_text="", **kwargs):
        super().__init__(*args, **kwargs)
        self.setObjectName("about_window")
        self.setFixedSize(QtCore.QSize(550, 250))
        self.setWindowTitle(translate("About Window", "About"))

        frame_rect = self.frameGeometry()
        center_point = QtWidgets.QApplication.primaryScreen(
        ).availableGeometry().center()
        frame_rect.moveCenter(center_point)
        self.move(frame_rect.topLeft())

        self.layout = QtWidgets.QVBoxLayout(self)
        about_label = QtWidgets.QLabel(about_text, self)
        about_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.layout.addWidget(about_label)


class SettingsWindow(QtWidgets.QWidget):
    """
    The dialog box that allows the user to change various parameters and settings
    """
    settings_save_requested = QtCore.pyqtSignal(dict)

    def __init__(self, *args, settings_data={}, **kwargs):
        super().__init__(*args, **kwargs)
        self.setObjectName("settings_window")
        self.setMinimumSize(QtCore.QSize(400, 300))
        size_policy = QtWidgets.QSizePolicy(
            QtWidgets.QSizePolicy.Policy.Expanding,
            QtWidgets.QSizePolicy.Policy.Expanding)
        size_policy.setHorizontalStretch(1)
        size_policy.setVerticalStretch(1)
        self.setSizePolicy(size_policy)
        self.setWindowTitle(translate("Settings Window", "Settings"))

        frame_rect = self.frameGeometry()
        center_point = QtWidgets.QApplication.primaryScreen(
        ).availableGeometry().center()
        frame_rect.moveCenter(center_point)
        self.move(frame_rect.topLeft())

        self.layout = QtWidgets.QVBoxLayout(self)
        self.settings_area = SettingsArea(self,
                                          settings_data=settings_data,
                                          fields_to_display=sorted(
                                              settings_data.keys()))
        self.layout.addWidget(self.settings_area)
        self.layout.setAlignment(self.settings_area,
                                 QtCore.Qt.AlignmentFlag.AlignCenter)

        self.settings_area.settings_save_requested.connect(
            self.settings_save_requested.emit)


class MainWindow(QtWidgets.QMainWindow):
    # For anytime a feature is changed (including by other Pigeon istances: they would trigger this signal).
    featureChanged = QtCore.pyqtSignal(BaseFeature)
    # For anytime this Pigeon instance triggers feature change: will result in syncing to other Pigeons.
    featureChangedLocally = QtCore.pyqtSignal(BaseFeature)
    # Same as featureChanged but for new features.
    featureAdded = QtCore.pyqtSignal(BaseFeature)
    # Same as featureChangedLocally but for new featuers.
    featureAddedLocally = QtCore.pyqtSignal(BaseFeature)

    settings_save_requested = QtCore.pyqtSignal(dict)

    def __init__(self,
                 uav,
                 settings_data={},
                 features=[],
                 about_text="",
                 exit_cb=noop):
        super().__init__()
        self.uav = uav
        self.settings_data = settings_data
        self.features = features
        self.about_text = about_text
        self.exit_cb = exit_cb

        self.about_window = None
        self.settings_window = None
        self.mavlinkdebugger_window = MavLinkDebugger()

        # State
        self.collect_subfeature_for = None
        self.current_image = None

        # Defining window properties
        self.setObjectName("main_window")
        self.showMaximized()
        self.setMinimumSize(QtCore.QSize(500, 500))
        size_policy = QtWidgets.QSizePolicy(
            QtWidgets.QSizePolicy.Policy.Expanding,
            QtWidgets.QSizePolicy.Policy.Expanding)
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
        self.main_vertical_split.setOrientation(QtCore.Qt.Orientation.Vertical)
        self.main_vertical_split.setObjectName("main_vertical_split")
        self.grid_layout.addWidget(self.main_vertical_split, 0, 0, 1, 1)

        self.main_horizontal_split = QtWidgets.QSplitter(
            self.main_vertical_split)
        self.main_horizontal_split.setOrientation(
            QtCore.Qt.Orientation.Horizontal)
        self.main_horizontal_split.setObjectName("main_horizontal_split")
        size_policy = QtWidgets.QSizePolicy(
            QtWidgets.QSizePolicy.Policy.MinimumExpanding,
            QtWidgets.QSizePolicy.Policy.Preferred)
        size_policy.setHorizontalStretch(0)
        size_policy.setVerticalStretch(100)
        self.main_horizontal_split.setSizePolicy(size_policy)
        self.main_horizontal_split.setMinimumSize(
            QtCore.QSize(200, THUMBNAIL_AREA_START_HEIGHT))

        # Populating the page layout with the major components.
        self.info_area = InfoArea(uav,
                                  self.main_horizontal_split,
                                  settings_data=settings_data,
                                  minimum_width=INFO_AREA_MIN_WIDTH)
        self.main_image_area = MainImageArea(self.main_horizontal_split,
                                             settings_data=settings_data,
                                             features=features)
        self.feature_area = FeatureArea(self.main_horizontal_split,
                                        settings_data=settings_data,
                                        minimum_width=FEATURE_AREA_MIN_WIDTH)
        self.thumbnail_area = ThumbnailArea(
            self.main_vertical_split,
            settings_data=settings_data,
            minimum_height=THUMBNAIL_AREA_MIN_HEIGHT)

        # Hooking up some inter-component behaviour.
        self.thumbnail_area.contents.currentItemChanged.connect(
            lambda new_item, old_item: self.showImage(new_item.image)
        )  # Show the image that's selected
        self.main_image_area.image_clicked.connect(self.handleMainImageClick)

        self.info_area.settings_area.settings_save_requested.connect(
            self.settings_save_requested.emit)
        # self.main_image_area.ruler.ruler_updated.connect(self.info_area.ruler_updated)

        # Hooking up feature inter-component behaviour. Listing all things we could do to change a
        # feature and hooking them up internally and externally
        for slot in [
                self.feature_area.feature_detail_area.
                featureChanged,  # Feature's details can be changed
                # Feature's position can be changed when it's dragged
                self.main_image_area.featureChanged,
        ]:
            # To let other components within this Pigeon know.
            slot.connect(self.featureChanged.emit)
            # To let other Pigeon's know.
            slot.connect(self.featureChangedLocally.emit)

        # These are the components that need to know when a feature is changed:
        # Update the feature in the list
        self.featureChanged.connect(self.feature_area.updateFeature)
        # Update the feature in the main image window
        self.featureChanged.connect(self.main_image_area.updateFeature)
        # Update the feature details
        self.featureChanged.connect(
            self.feature_area.feature_detail_area.updateFeature)

        # And things that need to know when a new feature is added, whether initiated by this Pigeon or another instance:
        for signal in [self.featureAdded, self.featureAddedLocally]:
            signal.connect(lambda feature: self.features.append(feature))
            signal.connect(self.main_image_area.addFeature)
            signal.connect(self.feature_area.addFeature)

        self.featureAddedLocally.connect(self.feature_area.showFeature)

        self.initMenuBar()
        QtCore.QMetaObject.connectSlotsByName(self)

    def initMenuBar(self):
        """
        Initializes File, Edit, Help navigation buttons
        """
        self.menubar = self.menuBar()
        self.menubar.setNativeMenuBar(False)

        menu = self.menubar.addMenu("&File")

        exit_action = QtGui.QAction("Exit", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.exit_cb)
        menu.addAction(exit_action)

        menu = self.menubar.addMenu("&Edit")
        settings_action = QtGui.QAction("Settings", self)
        settings_action.triggered.connect(self.showSettingsWindow)
        menu.addAction(settings_action)

        menu = self.menubar.addMenu("&Tools")

        about_action = QtGui.QAction("Mavlink Debugger", self)
        about_action.triggered.connect(self.displayMavlinkDebugger)
        menu.addAction(about_action)

        menu = self.menubar.addMenu("&Help")

        about_action = QtGui.QAction("About Pigeon", self)
        about_action.setShortcut("Ctrl+A")
        about_action.triggered.connect(self.showAboutWindow)
        menu.addAction(about_action)

        # Process Menu Bar
        # ===============

        # Extra Processing for images, like QR codes
        menu = self.menubar.addMenu("&Process")

        process_action = QtGui.QAction("Process QR Code", self)
        process_action.triggered.connect(self.decodeQR)

        # Activate only on first image load
        process_action.setEnabled(False)
        self.main_image_area.imageChanged.connect(
            lambda: process_action.setEnabled(True))

        menu.addAction(process_action)

    def displayMavlinkDebugger(self):
        self.mavlinkdebugger_window.show()

    def showAboutWindow(self):
        self.about_window = AboutWindow(about_text=self.about_text)
        self.about_window.show()

    def showSettingsWindow(self):
        self.settings_window = SettingsWindow(settings_data=self.settings_data)
        self.settings_window.show()
        self.settings_window.settings_save_requested.connect(
            self.settings_save_requested.emit)

    def reloadImages(self):
        self.addImage(Image("./data/images/1523.jpg",
                            "./data/images/1523.txt"))
        self.settings_window = SettingsWindow(settings_data=self.settings_data)
        self.settings_window.show()
        self.settings_window.settings_save_requested.connect(
            self.settings_save_requested.emit)

    def decodeQR(self):
        """
        Decode the QR code on the current image and then
        create a dialog box showing result
        """

        im_path = self.main_image_area.getImage().path
        QrDiag(self, im_path)

    def addImage(self, image: Image):
        """
        Initializes image and adds images to the thumbnail and info areas on the UI.
        If 'Follow Images' is not found within settings_data, or if no images is loaded, the
        image is shown on the main window.

        Parameters:
            image (Image): image to be added to UI
        """
        try:
            image.pixmap_loader = PixmapLoader(image)

            # Recording the width and height of the image for other code to use:
            image.width = image.pixmap_loader.width()
            image.height = image.pixmap_loader.height()

            if self.settings_data.get("Follow Images",
                                      False) or not self.current_image:
                self.showImage(image)
            self.thumbnail_area.addImage(image)
            self.info_area.addImage(image)
            image.pixmap_loader.optimizeMemory()
        except Exception as err:
            print(f"WARN: Error parsing image\n{err}")

    def setSettings(self, settings_data):
        return self.info_area.setSettings(settings_data)

    def showImage(self, image: Image):
        """
        Frees memory from old image and initialize selected image. Propagating image to main image area
        and info areas on the UI.

        Parameters:
            image (Image): selected image
        """
        if self.current_image:
            self.current_image.pixmap_loader.freeOriginal()
            self.current_image.pixmap_loader.optimizeMemory()
        self.current_image = image
        self.current_image.pixmap_loader.holdOriginal()
        self.main_image_area.showImage(image)
        self.info_area.showImage(image)

    def createNewMarker(self, image: Image, point: Point):
        """
        Initiallizes a marker and creates a cropped image of it. Emits a featureAddedLocally signal.

        Parameters:
            image (Image): image contantaining marker
            point (Point): pixel location of marker on image
        """
        marker = Marker(image, point=(point.x(), point.y()))
        self.featureAddedLocally.emit(marker)

    def collectSubfeature(self, feature):
        # ??
        self.collect_subfeature_for = feature

    def handleMainImageClick(self, image: Image, point: Point):
        """
        Checks if clicked region on an image is a marker or subfeature.

        Parameters:
            image (Image): clicked image
            point (Point): pixel location from which the image was clicked
        """
        if self.collect_subfeature_for:
            self.collect_subfeature_for.updatePoint(image,
                                                    (point.x(), point.y()))
            self.featureChanged.emit(self.collect_subfeature_for)
            self.collect_subfeature_for = None
        else:
            self.createNewMarker(image, point)

    def closeEvent(self, event):
        self.exit_cb(
        )  # Terminating the whole program if the main window is closed
