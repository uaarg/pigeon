from PyQt5 import QtCore, QtGui, QtWidgets
translate = QtCore.QCoreApplication.translate
import datetime
import json

from ..commonwidgets import NonEditableBaseListForm, BoldQLabel

from ..ui import icons
from ..common import format_duration_for_display

def markMessageReceived(func=None):
    """
    Marks that a message has been received from the UAV. Function
    decorator for methods who's class has a last_message_received_time
    attribute.
    """
    def new_func(*args, **kwargs):
        args[0].last_message_received_time = datetime.datetime.now()
        func(*args, **kwargs)
    return new_func

class ControlsArea(QtWidgets.QWidget):
    send_command = QtCore.pyqtSignal(str, str)
    receive_command_ack = QtCore.pyqtSignal(str, str)
    receive_status_message = QtCore.pyqtSignal(str)

    uav_connection_changed = QtCore.pyqtSignal(bool)

    RUN_STOP = "0"
    RUN_PAUSE = "1"
    RUN_PLAY = "2"

    RUN_CHOICES = ((RUN_STOP, "Stopped"),
                   (RUN_PAUSE, "Paused"),
                   (RUN_PLAY, "Running"))

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.layout = QtWidgets.QVBoxLayout(self)

        self.title = BoldQLabel(self)
        self.title.setText(translate("ControlsArea", "UAV:"))
        self.layout.addWidget(self.title)

        self.uav_status_form = NonEditableBaseListForm()
        self.layout.addWidget(self.uav_status_form)

        self.uav_connected = "No"
        self.last_message_received_time = None
        self.uav_pictures_taken = ""
        self.uav_pictures_transmitted = ""

        run_buttons_layout = QtWidgets.QHBoxLayout()
        self.layout.addLayout(run_buttons_layout)

        self.run_value = self.RUN_STOP
        self.play_icon = QtGui.QIcon(icons.play)
        self.pause_icon = QtGui.QIcon(icons.pause)

        self.stop_button = QtWidgets.QPushButton(QtGui.QIcon(icons.stop), "", self)
        self.stop_button.clicked.connect(self.stop_button_clicked)
        run_buttons_layout.addWidget(self.stop_button)

        self.play_pause_button = QtWidgets.QPushButton(self.play_icon, "", self)
        self.play_pause_button.clicked.connect(self.play_pause_button_clicked)
        run_buttons_layout.addWidget(self.play_pause_button)

        self.run_value_label = QtWidgets.QLabel()
        run_buttons_layout.addWidget(self.run_value_label)

        self.receive_command_ack.connect(self.receiveCommandAck)
        self.uav_connection_changed.connect(self.updateUAVConnection)
        self.receive_status_message.connect(self.receiveStatusMessage)

        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self._updateDisplayedInfo)
        self.timer.start(1000)

    def stop_button_clicked(self):
        self.send_command.emit("RUN", self.RUN_STOP)

    def play_pause_button_clicked(self):
        new_value = self._getToggledRunValue()
        self.send_command.emit("RUN", new_value)

    def _updateRunValue(self, value):
        if value != self.RUN_PLAY:
            self.play_pause_button.setIcon(self.play_icon)
        else:
            self.play_pause_button.setIcon(self.pause_icon)

        if value == self.RUN_STOP:
            self.stop_button.setEnabled(False)
        else:
            self.stop_button.setEnabled(True)

        self.run_value = value

        self.run_value_label.setText(self.get_RUN_display())

    def _getToggledRunValue(self):
        if self.run_value == self.RUN_PLAY:
            return self.RUN_PAUSE
        else:
            return self.RUN_PLAY

    def get_RUN_display(self):
        return dict(self.RUN_CHOICES).get(self.run_value)

    @markMessageReceived
    def receiveCommandAck(self, command, value):
        if command == "RUN":
            self._updateRunValue(value)

    def _updateDisplayedInfo(self):
        if self.last_message_received_time:
            time_since_last_message = format_duration_for_display(datetime.datetime.now() - self.last_message_received_time)
        else:
            time_since_last_message = "(never)"
        data = [("UAV Connected", self.uav_connected),
                ("Time since last message", time_since_last_message),
                ("Pictures captured", self.uav_pictures_taken),
                ("Pictures transmitted", self.uav_pictures_transmitted),
               ]
        self.uav_status_form.setData(data)

    def updateUAVConnection(self, connected):
        if connected:
            self.uav_connected = "Yes"
        else:
            self.uav_connected = "No"
        self._updateDisplayedInfo()

    @markMessageReceived
    def receiveStatusMessage(self, status):
        self._updateDisplayedInfo()
        try:
            status_dict = json.loads(status)
            self.uav_pictures_taken = str(status_dict.get("TAKEN", ""))
            self.uav_pictures_transmitted = str(status_dict.get("TRANS", ""))
        except Exception:
            pass
