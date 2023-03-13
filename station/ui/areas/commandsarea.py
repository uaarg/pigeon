from PyQt5 import QtCore, QtGui, QtWidgets
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
    send_command = QtCore.pyqtSignal(str, str)
    receive_command_ack = QtCore.pyqtSignal(str, str)
    

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.layout = QtWidgets.QGridLayout(self)

        # Auto-Landing Approval
        # =============

        # Label
        self.allowLandLabel = BoldQLabel()
        self.allowLandLabel.setText("Approve Auto-Land")
        self.layout.addWidget(self.allowLandLabel, 1, 1)

        # Buttons
        self.aproveLandBtn = QtWidgets.QPushButton("Yes")
        self.aproveLandBtn.clicked.connect(lambda: self.send_command.emit("ALLOW_LANDING", '1'))
        self.layout.addWidget(self.aproveLandBtn, 1, 2)

        self.disallowLandBtn = QtWidgets.QPushButton("No")
        self.disallowLandBtn.clicked.connect(lambda: self.send_command.emit("ALLOW_LANDING", '0'))
        self.layout.addWidget(self.disallowLandBtn, 1, 3)

        # Resend Last Image
        # =============

        # Label
        self.resendLabel = BoldQLabel()
        self.resendLabel.setText("Resend Last Image")
        self.layout.addWidget(self.resendLabel, 2, 1)

        # Buttons
        self.resendBtn = QtWidgets.QPushButton("Resend")
        self.resendBtn.clicked.connect(lambda: self.send_command.emit("RESEND_IMAGE", '0'))
        self.layout.addWidget(self.resendBtn, 2, 3)

        # Stop Search Pattern
        # =============

        # Label
        self.autoNavLabel = BoldQLabel()
        self.autoNavLabel.setText("Allow Auto-Nav")
        self.layout.addWidget(self.autoNavLabel, 3, 1)

        # Buttons
        self.resendBtn = QtWidgets.QPushButton("GO")
        self.resendBtn.clicked.connect(lambda: self.send_command.emit("ALLOW_AUTONAV", '1'))
        self.layout.addWidget(self.resendBtn, 3, 2)

        self.disallowBtn = QtWidgets.QPushButton("STOP")
        self.disallowBtn.clicked.connect(lambda: self.send_command.emit("ALLOW_AUTONAV", '0'))
        self.layout.addWidget(self.disallowBtn, 3, 3)

        # Hook up our slots
        self.receive_command_ack.connect(self.receiveCommandAck) # Emit in UI

    @markMessageReceived
    def receiveCommandAck(self, command, value):
        print("Command Ack")
