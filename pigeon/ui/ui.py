import sys
import logging
import signal as signal_  # For exiting pigeon from terminal
from queue import Queue
from time import time

from PyQt6 import QtCore, QtWidgets, QtGui

translate = QtCore.QCoreApplication.translate  # Potential aliasing

from pigeon.ui.areas import InfoArea, ThumbnailArea, MessageLogArea, MainImageArea, SettingsArea
from pigeon.ui.common import QueueMixin
from pigeon.ui.pixmaploader import PixmapLoader
from pigeon.ui.style import stylesheet

from pigeon.image import Image
from pigeon.comms.services.messageservice import MavlinkMessage

THUMBNAIL_AREA_START_HEIGHT = 100
THUMBNAIL_AREA_MIN_HEIGHT = 60
INFO_AREA_MIN_WIDTH = 250
MESSAGE_LOG_AREA_MIN_WIDTH = 300


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
                 statustext_in_queue,
                 about_text=""):
        super().__init__()

        # Init
        # ====
        self.logger = logging.getLogger(__name__ + "." +
                                        self.__class__.__name__)
        self.settings_data = load_settings()
        self.uav = uav
        self.save_settings = save_settings

        self.app = QtWidgets.QApplication(sys.argv)
        self.app.setStyleSheet(stylesheet)
        self.main_window = MainWindow(self.uav, self.settings_data, about_text,
                                      self.app.exit)

        self.main_window.settings_save_requested.connect(
            self.settings_changed.emit)

        self.connectSignals(image_in_queue, message_in_queue,
                            statustext_in_queue)

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

    def connectSignals(self, image_in_queue: Queue, message_in_queue: Queue,
                       statustext_in_queue: Queue):
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
        self.connectQueue(image_in_queue, self.addImage)
        self.connectQueue(
            message_in_queue,
            self.main_window.mavlinkdebugger_window.handleMessage)
        self.connectQueue(statustext_in_queue,
                          self.main_window.message_log_area.queueMessage)

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
        self.number_of_messages = 0
        self.current_message_number = 1

        layout = QtWidgets.QVBoxLayout(self)
        layout.addWidget(self.message_display)

        self.receive_message.connect(self.handleMessage)

    def handleMessage(self, message: MavlinkMessage):
        current_time = message.time.strftime("%H:%M:%S")
        self.message_display.append(
            f"{self.current_message_number}.  Message: {message.type}, Received: {current_time}"
        )
        self.current_message_number += 1
        self.number_of_messages += 1
        if self.number_of_messages == 50000:
            self.message_display.clear()
            self.number_of_messages = 0


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
    settings_save_requested = QtCore.pyqtSignal(dict)

    receive_message = QtCore.pyqtSignal(MavlinkMessage)

    def __init__(self, uav, settings_data={}, about_text="", exit_cb=noop):
        super().__init__()
        self.uav = uav
        self.settings_data = settings_data
        self.about_text = about_text
        self.exit_cb = exit_cb

        self.about_window = None
        self.settings_window = None
        self.mavlinkdebugger_window = MavLinkDebugger()

        # State
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
                                             settings_data=settings_data)
        self.message_log_area = MessageLogArea(
            self.main_horizontal_split,
            minimum_width=MESSAGE_LOG_AREA_MIN_WIDTH)
        self.receive_message.connect(self.message_log_area.queueMessage)

        self.thumbnail_area = ThumbnailArea(
            self.main_vertical_split,
            settings_data=settings_data,
            minimum_height=THUMBNAIL_AREA_MIN_HEIGHT)

        # Hooking up some inter-component behaviour.
        self.thumbnail_area.contents.currentItemChanged.connect(
            lambda new_item, old_item: self.showImage(new_item.image)
        )  # Show the image that's selected

        self.info_area.settings_area.settings_save_requested.connect(
            self.settings_save_requested.emit)

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

    def closeEvent(self, event):
        self.exit_cb(
        )  # Terminating the whole program if the main window is closed
