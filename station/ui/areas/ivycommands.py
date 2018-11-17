from PyQt5 import QtCore, QtGui, QtWidgets

class IvyCommander(QtWidgets.QWidget):
    """
    Sends various commands to the UAV via the ivybus.
    For commands, see transmissions.h in waldo
    Not actually a real area in the ui. Its main funcitonality is in the topbar.
    """
    
    # This is how we send commands in the plane. Hooked up in ui.py
    send_command = QtCore.pyqtSignal(str, str)

    def generate_change_shutter(self, amount = 1):
        """
        Generates a function that sends a command to change shutter speed.
        i.e. Increment/decrement
        """
        
        change_shutter = lambda: self.send_command.emit("CHANGE_SHUTTER_SPEED", str(amount))
        return change_shutter

    
    def generate_set_shutter(self, amount = 1):
        """
        Creates and returns a function that sends command
        to set the UAV's shutter speed to a discrete value
        """

        set_shutter = lambda: self.send_command.emit("SHUTTER_SPEED", str(amount))
        return set_shutter

    def custom_command(self):
        """
        Sends a typed up command to the UAV
        """
        pass