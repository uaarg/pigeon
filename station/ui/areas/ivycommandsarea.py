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

class IvyCommandsArea(QtWidgets.QWidget):
    """
    Sends various commands to the UAV via the ivybus.
    Controls many aspects relating to camera behavior
    For commands, see transmissions.h in waldo
    """
    # This is how we send commands in the plane. Hooked up in ui.py
    send_command = QtCore.pyqtSignal(str, str)
    receive_command_ack = QtCore.pyqtSignal(str, str)
    

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.layout = QtWidgets.QGridLayout(self)

        # Shutter Speed
        # =============

        # Label
        self.title = BoldQLabel()
        self.title.setText("Shutter Speed")
        self.layout.addWidget(self.title, 1, 1)

        # Buttons
        self.upBtn = QtWidgets.QPushButton("Up")
        self.upBtn.clicked.connect(self.generateChangeShutter(5))
        self.layout.addWidget(self.upBtn, 1, 2)

        self.downBtn = QtWidgets.QPushButton("Down")
        self.downBtn.clicked.connect(self.generateChangeShutter(-5))
        self.layout.addWidget(self.downBtn, 1, 3)

        # Hook up our slots
        self.receive_command_ack.connect(self.receiveCommandAck) # Emit in UI


    def generateChangeShutter(self, amount = 1):
        """
        Generates a function that sends a command to change shutter speed.
        i.e. Increment/decrement
        For use with b
        Parameters:
            int amount The amount to change the shutter speed by
                       Can be negative.
        """
        
        change_shutter = lambda: self.send_command.emit("CHANGE_SHUTTER_SPEED", str(amount))
        return change_shutter

    
    def generateSetShutter(self, amount = 1):
        """
        Creates and returns a function that sends command
        to set the UAV's shutter speed to a discrete value
        """

        set_shutter = lambda: self.send_command.emit("SHUTTER_SPEED", str(amount))
        return set_shutter


    @markMessageReceived
    def receiveCommandAck(self, command, value):
        print("Command Ack")
