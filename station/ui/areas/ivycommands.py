from PyQt5 import QtCore, QtGui, QtWidgets

class ivy_commander():
    """
    Sends various commands to the UAV via the ivybus.
    """
    
    send_command = QtCore.pyqtSignal(str, str)

    def up_shutter_speed(self, amount = 5):
        """
        Sends the command to increase the shutter speed
        """
        pass

    def down_shutted_speed(self, amount = 5):
        """
        Sends the command to decrease the shutter speed
        """
        pass

    def custom_command(self):
        """
        Sends a typed up command to the UAV
        """
        pass