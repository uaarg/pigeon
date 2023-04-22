from PyQt5 import QtCore, QtGui, QtWidgets
from comms.services.command import Command
from ..commonwidgets import NonEditableBaseListForm, BoldQLabel

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

class CommandsArea(QtWidgets.QWidget):
    """
    Sends various commands to the UAV.
    Controls many aspects relating to camera behavior
    For commands, see transmissions.h in waldo
    """
    # This is how we send commands in the plane. Hooked up in ui.py
    send_command = QtCore.pyqtSignal(Command)
    receive_command_ack = QtCore.pyqtSignal(str, str)
    

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.layout = QtWidgets.QGridLayout(self)

        # Auto-Landing Approval
        # =============

        # # Label
        # self.allowLandLabel = BoldQLabel()
        # self.allowLandLabel.setText("Approve Auto-Land")
        # self.layout.addWidget(self.allowLandLabel, 1, 1)

        # # Buttons
        # self.aproveLandBtn = QtWidgets.QPushButton("Yes")
        # self.aproveLandBtn.clicked.connect(lambda: self.send_command.emit("ALLOW_LANDING", '1'))
        # self.layout.addWidget(self.aproveLandBtn, 1, 2)

        # self.disallowLandBtn = QtWidgets.QPushButton("No")
        # self.disallowLandBtn.clicked.connect(lambda: self.send_command.emit("ALLOW_LANDING", '0'))
        # self.layout.addWidget(self.disallowLandBtn, 1, 3)

        # Resend Last Image
        # =============

        # Label
        self.resendLabel = BoldQLabel()
        self.resendLabel.setText("Resend Last Image")
        self.layout.addWidget(self.resendLabel, 2, 1)

        # Buttons
        self.resendBtn = QtWidgets.QPushButton("Resend")
        self.resendBtn.clicked.connect(lambda: self.send_command.emit(
            Command.sendImage()
        ))
        self.layout.addWidget(self.resendBtn, 2, 3)

        # Stop Search Pattern
        # =============

        # # Label
        # self.autoNavLabel = BoldQLabel()
        # self.autoNavLabel.setText("Allow Auto-Nav")
        # self.layout.addWidget(self.autoNavLabel, 3, 1)

        # # Buttons
        # self.resendBtn = QtWidgets.QPushButton("GO")
        # self.resendBtn.clicked.connect(lambda: self.send_command.emit("ALLOW_AUTONAV", '1'))
        # self.layout.addWidget(self.resendBtn, 3, 2)

        # self.disallowBtn = QtWidgets.QPushButton("STOP")
        # self.disallowBtn.clicked.connect(lambda: self.send_command.emit("ALLOW_AUTONAV", '0'))
        # self.layout.addWidget(self.disallowBtn, 3, 3)

        # Camera Capture ON?OFF
        # =============

        # Label
        self.camCaptureLabel = BoldQLabel()
        self.camCaptureLabel.setText("Camera Capture")
        self.layout.addWidget(self.camCaptureLabel, 4, 1)

        # Buttons
        self.enableCamCaptureBtn = QtWidgets.QPushButton("ON")
        self.enableCamCaptureBtn.clicked.connect(lambda: self.send_command.emit(
            Command.enableCamera()
        ))
        self.layout.addWidget(self.enableCamCaptureBtn, 4, 2)

        self.disableCamCaptureBtn = QtWidgets.QPushButton("OFF")
        self.disableCamCaptureBtn.clicked.connect(lambda: self.send_command.emit(
            Command.disableCamera()
        ))
        self.layout.addWidget(self.disableCamCaptureBtn, 4, 3)

        # Mode Control
        # =============

        # Label
        self.modeControlLabel = BoldQLabel()
        self.modeControlLabel.setText("Mode Control")
        self.layout.addWidget(self.modeControlLabel, 5, 1)

        # Dropdown
        self.modeControlDropdown = QtWidgets.QComboBox()
        self.modeControlDropdown.addItems(['IDLE', 'TAKEOFF', 'FOLLOW_MISSION', 'LANDING_SEARCH', 'LAND'])
        self.layout.addWidget(self.modeControlDropdown, 5, 2)

        # Button
        self.modeControlBtn = QtWidgets.QPushButton("SEND")
        self.modeControlBtn.clicked.connect(lambda: self.send_command.emit(
            Command.setMode(self.modeControlDropdown.currentIndex())
        ))
        self.layout.addWidget(self.modeControlBtn, 5, 3)

        # LIGHTS ON?OFF
        # =============

        # Label
        self.lightControlLabel = BoldQLabel()
        self.lightControlLabel.setText("Onboard LEDs")
        self.layout.addWidget(self.lightControlLabel, 6, 1)

        # Buttons
        self.lightControlOnBtn = QtWidgets.QPushButton("ON")
        self.lightControlOnBtn.clicked.connect(lambda: self.send_command.emit(
            Command.switchLights(True)
        ))
        self.layout.addWidget(self.lightControlOnBtn, 6, 2)

        self.lightControlOffBtn = QtWidgets.QPushButton("OFF")
        self.lightControlOffBtn.clicked.connect(lambda: self.send_command.emit(
            Command.switchLights(False)
        ))
        self.layout.addWidget(self.lightControlOffBtn, 6, 3)

        # Hook up our slots
        self.receive_command_ack.connect(self.receiveCommandAck) # Emit in UI

    @markMessageReceived
    def receiveCommandAck(self, command, value):
        print("Command Ack")
