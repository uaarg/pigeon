import datetime

from PyQt5 import QtCore, QtGui, QtWidgets
translate = QtCore.QCoreApplication.translate

from ..commonwidgets import NonEditableBaseListForm
from ..common import format_duration_for_display

from . import ControlsArea
from . import SettingsArea
from .ivycommandsarea import IvyCommandsArea

class ImageInfoArea(NonEditableBaseListForm):
    # Removed title so that the image info tab doesn't
    # have a gigantic second title.
    pass

class StateArea(NonEditableBaseListForm):
    def _title(self):
        return "State:"


class InfoArea(QtWidgets.QFrame):
    def __init__(self, *args, settings_data={}, minimum_width=250, **kwargs):
        super().__init__(*args, **kwargs)

        size_policy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.MinimumExpanding)
        size_policy.setHorizontalStretch(0)
        size_policy.setVerticalStretch(0)
        self.setSizePolicy(size_policy)
        self.setMinimumSize(QtCore.QSize(minimum_width, 200))

        self.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.setFrameShadow(QtWidgets.QFrame.Raised)
        self.setObjectName("info_area")

        self.layout = QtWidgets.QVBoxLayout(self)

        # Create tabs for controls
        self.tabWidget = QtWidgets.QTabWidget()

        self.ivyTab = self.createTab("Ivy Tab")
        self.pigeonTab = self.createTab("Pigeon Tab")
        self.imageInfoTab = self.createTab("Image Info")

        # Create Controls and add to respective tabs
        self.controls_area = ControlsArea(self)

        self.image_info_area = ImageInfoArea(self.imageInfoTab, editable=False)
        self.imageInfoTab.layout.addWidget(self.image_info_area)

        self.state_area = StateArea(self.pigeonTab, editable=False)
        self.settings_area = SettingsArea(self.pigeonTab, 
            settings_data=settings_data, 
            fields_to_display=["Follow Images", "Plane Plumbline"])
        self.pigeonTab.layout.addWidget(self.state_area)
        self.pigeonTab.layout.addWidget(self.settings_area)

        self.ivyControls = IvyCommandsArea(self)
        self.ivyTab.layout.addWidget(self.ivyControls)

        # Add parent widgets to info area
        self.layout.addWidget(self.controls_area)
        self.layout.addWidget(self.tabWidget)

        self.last_image_time = None
        self.image_count = 0

        # Starting a timer to update data every second
        self._updateInfo()
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self._updateInfo)
        self.timer.start(1000)
    
    def createTab(self, name):
        """
        Creates and returns a tab with a layout widget
        Also assigns tab to its proper parent (Tab Widget)
        """
        tab = QtWidgets.QWidget()
        tab.layout = QtWidgets.QVBoxLayout(tab)
        self.tabWidget.addTab(tab, name)
        return tab

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
            last_image_time_ago = format_duration_for_display(timedelta)
        else:
            last_image_time_ago = "(none received)"

        data = [("Image Count", str(self.image_count)),
                ("Time since last image", last_image_time_ago),]
        self.state_area.setData(data)
